import hashlib
from functools import wraps
from typing import Any, get_args, Callable

from django.apps import apps
from django.core.cache import cache
from django.db.models import Model as DjangoModel
from pydantic import BaseModel as PydanticModel


# get the cache key for storage
def cache_get_key(*args, **kwargs) -> str:
    serialise = []
    for arg in args:
        serialise.append(str(arg))
    for key, arg in kwargs.items():
        serialise.append(str(key))
        serialise.append(str(arg))
    key = hashlib.md5(":".join(serialise).encode("utf-8")).hexdigest()
    return key


# decorator for caching functions
def cache_for(seconds: int | float, cache_none: bool = True) -> Callable:
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = cache_get_key(fn.__module__ + "." + fn.__name__, *args, **kwargs)
            if cached_result := cache.get(key):
                return _deserialize(
                    cached_result,
                    _get_all_pydantic_models(fn.__annotations__.get("return")),
                )

            result = fn(*args, **kwargs)

            if not cache_none and result is None:
                raise ValueError("Can't cache null value")

            cache.set(key, _serialize(result), seconds)

            return result

        return wrapper

    return decorator


_NONE_VALUE = {"__none__": True}


def _serialize(data: Any, depth: int = 0) -> Any:
    if data is None and depth == 0:
        return _NONE_VALUE

    if isinstance(data, PydanticModel):
        return {"__pydantic__": data.__class__.__name__, "data": data.dict()}

    elif isinstance(data, DjangoModel):
        app_name = data._meta.app_label  # type: ignore
        model_name = data._meta.model_name  # type: ignore
        return {
            "__django__": {"app_name": app_name, "model_name": model_name},
            "pk": data.pk,
        }

    elif isinstance(data, (list, tuple)):
        return [_serialize(item, depth + 1) for item in data]

    elif isinstance(data, dict):
        return {key: _serialize(value, depth + 1) for key, value in data.items()}

    return data


def _get_all_pydantic_models(data_type: Any) -> dict[str, PydanticModel]:
    if data_type is None:
        return {}

    if isinstance(data_type, type) and issubclass(data_type, PydanticModel):
        return {data_type.__name__: data_type}  # type: ignore

    result = {}
    for cls in get_args(data_type):
        result.update(_get_all_pydantic_models(cls))
    return result


def _deserialize(data: Any, pydantic_models: dict) -> Any:
    if data == _NONE_VALUE:
        return None

    if isinstance(data, dict) and "__pydantic__" in data:
        if cls := pydantic_models.get(data["__pydantic__"]):
            return cls(**data["data"])
        raise ValueError(f"Can't find pydantic model {data['__pydantic__']}")

    elif isinstance(data, dict) and "__django__" in data:
        app_name = data["__django__"]["app_name"]
        model_name = data["__django__"]["model_name"]
        pk = data["pk"]
        ModelClass = apps.get_model(app_name, model_name)
        return ModelClass.objects.get(pk=pk)

    elif isinstance(data, (list, tuple)):
        return [_deserialize(item, pydantic_models) for item in data]

    elif isinstance(data, dict):
        return {
            key: _deserialize(value, pydantic_models) for key, value in data.items()
        }

    return data
