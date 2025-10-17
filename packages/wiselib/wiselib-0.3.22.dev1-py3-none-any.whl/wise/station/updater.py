import json
import logging
from abc import abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, TypeVar, Generic, Self, Any, Callable, Iterable
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.timezone import make_aware
from pydantic import BaseModel, ValidationError
from redis.exceptions import LockError
from rest_framework.serializers import SerializerMetaclass

from wise.station.heap import ReplicatedHashHeap
from wise.utils.http_requests import HTTPClient
from wise.utils.models import BaseModel as DjangoBaseModel
from wise.utils.redis import get_redis_client
from wise.utils.cache import cache_get_key
from wise.utils.time import iso_serialize, iso_deserialize

ModelType = TypeVar("ModelType", bound=DjangoBaseModel)
BoundedType = TypeVar("BoundedType", bound=DjangoBaseModel)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager  # type: ignore

    RelatedManagerType = RelatedManager[ModelType]
else:
    RelatedManagerType = Any


class SkipUpdate(Exception):
    pass


class Updater:
    @abstractmethod
    def update(self):
        ...


class IterableUpdater(Updater):
    def __init__(self, col: Iterable[Updater]):
        self.col = col

    def update(self):
        for updater in self.col:
            updater.update()


class QuerysetUpdater(Updater):
    def __init__(self, qs: QuerySet):
        self.qs = qs

    def update(self):
        for updater in self.qs.all():
            updater.update()


class CacheUpdater(Updater):
    def __init__(
        self,
        queryset: QuerySet | Callable,
        serializer: SerializerMetaclass | Callable,
        cache_key_prefix: str,
        periodic_should_update_func: Callable | None = None,
        get_value_should_update_func: Callable | None = None,
        lock_timeout_seconds: int = 300,
    ):
        self.queryset = queryset
        self.serializer = serializer
        self.cache_key_prefix = cache_key_prefix
        if periodic_should_update_func is not None:
            self.periodic_should_update_func = periodic_should_update_func
        if get_value_should_update_func is not None:
            self.get_value_should_update_func = get_value_should_update_func
        self.lock_timeout_seconds = lock_timeout_seconds
        self.batch_size = 1000
        self.redis = get_redis_client()
        self.now = datetime.now()

    def update(self):
        try:
            with self.redis.lock(
                self.get_cache_key(), self.lock_timeout_seconds, blocking=False
            ):
                self._update()
        except LockError:
            ...

    def _update(self):
        self.now = datetime.now()
        start_index = 0
        if isinstance(self.queryset, QuerySet):
            all_objects = self.queryset.all()
            count = self.queryset.count()
        else:
            all_objects = self.queryset()
            count = len(all_objects)
        while start_index < count:
            query_set = all_objects[start_index : start_index + self.batch_size]
            start_index += self.batch_size
            last_update_keys = [
                self.get_last_update_timestamp_redis_key(instance)
                for instance in query_set
            ]
            last_update_timestamps = self.redis.mget(last_update_keys)
            for instance, last_update_timestamp in zip(
                query_set, last_update_timestamps
            ):
                try:
                    last_update = None
                    if last_update_timestamp is not None:
                        last_update = make_aware(
                            datetime.fromtimestamp(float(last_update_timestamp))
                        )  # type: ignore
                    if self.periodic_should_update(instance, last_update):
                        self.force_update(instance)
                except Exception:
                    logger.exception(f"could not cache {instance}")

    def periodic_should_update(
        self, instance, last_update: datetime | None = None
    ) -> bool:
        if last_update is None:
            last_update = self.get_last_update(instance)
        if self.periodic_should_update_func is None:
            return self.default_should_update(instance, last_update)
        return self.periodic_should_update_func(instance, last_update)

    def get_value_should_update(self, instance) -> bool:
        last_update = self.get_last_update(instance)
        if self.get_value_should_update_func is None:
            return self.default_should_update(instance, last_update)
        return self.get_value_should_update_func(instance, last_update)

    def default_should_update(self, instance, last_update: datetime | None) -> bool:
        return last_update is None or last_update < instance.updated_at

    def get_last_update(self, instance) -> datetime | None:
        last_update_timestamp = self.redis.get(
            self.get_last_update_timestamp_redis_key(instance)
        )
        if last_update_timestamp is None:
            return None
        return make_aware(
            datetime.fromtimestamp(float(last_update_timestamp))
        )  # type: ignore

    def get_value(self, instance):
        if self.get_value_should_update(instance):
            value = self.force_update(instance)
        else:
            value = self.redis.get(self.get_value_redis_key(instance))
            if value is None:
                value = self.force_update(instance)
        return json.loads(value)

    def force_update(self, instance) -> str:
        if isinstance(self.serializer, SerializerMetaclass):
            value = json.dumps(self.serializer(instance).data)
        else:
            value = json.dumps(self.serializer(instance))
        self.redis.set(self.get_value_redis_key(instance), value)
        self.redis.set(
            self.get_last_update_timestamp_redis_key(instance), self.now.timestamp()
        )
        return value

    def get_key(self, instance):
        if hasattr(instance, "key"):
            return instance.key
        return cache_get_key(instance)

    def get_last_update_timestamp_redis_key(self, instance) -> str:
        return f"{self.cache_key_prefix}:{self.get_key(instance)}:timestamp"

    def get_value_redis_key(self, instance) -> str:
        return f"{self.cache_key_prefix}:{self.get_key(instance)}:value"

    def get_cache_key(self) -> str:
        return f"{self.cache_key_prefix}:run_lock"


class ModelUpdater(BaseModel, Generic[ModelType], Updater):
    @abstractmethod
    def update(self) -> ModelType:
        ...


class BindingUpdater(BaseModel, Generic[ModelType, BoundedType]):
    @abstractmethod
    def update(self, bounded: BoundedType) -> ModelType:
        ...

    @classmethod
    def update_bindings(
        cls,
        *,
        updaters: list[Self],
        bounded: BoundedType,
        bindings: RelatedManagerType,  # type: ignore
    ) -> list[ModelType]:
        with transaction.atomic():
            instances = [u.update(bounded) for u in updaters]
            bindings.exclude(key__in=[i.key for i in instances]).delete()  # type: ignore
            return instances


class UpdaterHandler:
    def __init__(
        self,
        default_object_name: str | None = None,
        client: HTTPClient | None = None,
    ) -> None:
        self.handlers: dict[
            str, tuple[type[Updater], tuple[Callable[[Any], None], ...]]
        ] = {}
        self.default_object_name = default_object_name

        self.client = client
        if self.client:
            assert self.client.base_url, "base_url is not provided to HTTPClient"

    def add(
        self,
        object_name: str,
        updater_class: type[Updater],
        *callbacks: Callable[[Any], None],
    ) -> Self:
        assert object_name not in self.handlers
        self.handlers[object_name] = updater_class, callbacks
        return self

    def pull(self, name: str, **kwargs) -> list[Any]:
        assert self.client, "client is not provided to UpdaterHandler"
        resp = self.client.get(
            "station/publisher/query",
            params={"name": name, **kwargs},
        )
        resp.raise_for_status()
        resp_body = resp.json()
        results = resp_body["results"]
        instances = []

        for item in results:
            instance = self(item, default_name=name)
            if instance:
                instances.append(instance)

        return instances

    def pull_one(self, name: str, **kwargs) -> Any | None:
        instances = self.pull(name, **kwargs)
        if not instances:
            return None

        assert len(instances) == 1
        return instances[0]

    def get_heaps(self) -> Iterable[ReplicatedHashHeap]:
        for name, (updater_class, _) in self.handlers.items():
            heap = self._get_heap(name, updater_class)
            if heap:
                yield heap

    def _get_heap(
        self, name: str, updater_class: type[Updater]
    ) -> ReplicatedHashHeap | None:
        if self.client and getattr(updater_class, "heap_enabled", None):
            return ReplicatedHashHeap(
                name=name,
                get_node=lambda index: self._fetch_heap_node(name, index),
            )
        return None

    def _fetch_heap_node(self, name: str, index: int) -> dict:
        assert self.client
        resp = self.client.get(
            "station/heap/node",
            params={"name": name, "index": str(index)},
        )
        resp.raise_for_status()
        d = resp.json()
        self(d, update_heap=False, raise_exception=True)
        return d["heap_node"]

    def __call__(
        self,
        value,
        *,
        update_heap: bool = True,
        raise_exception: bool = False,
        default_name: str | None = None,
    ) -> Any | None:
        heap_node = None

        if "object_name" in value:
            name = value["object_name"]
            data = value["body"]
            heap_node = value.get("heap_node")

        elif default_name or self.default_object_name:
            name = default_name or self.default_object_name
            data = value
        else:
            logger.info("unknown object received")
            return None

        if name not in self.handlers:
            logger.info("unknown object received", extra={"object_name": name})
            return None

        updater_class, callbacks = self.handlers[name]

        def do_heap_update():
            if not heap_node or not update_heap:
                return
            heap = self._get_heap(heap_node["name"], updater_class)
            heap.update_node(int(heap_node["index"]), timeout=10)

        try:
            data["updater_handler"] = self
            updater = updater_class(**data)
        except ValidationError as e:
            if raise_exception:
                raise e
            logger.exception("invalid object received")
            return None

        try:
            instance = updater.update()
        except SkipUpdate:
            logger.info("update skipped")
            do_heap_update()
            return None

        if instance is None:
            do_heap_update()
            return None

        if isinstance(instance, DjangoBaseModel):
            logger.info(
                "object persisted",
                extra={
                    "model": instance.__class__.__name__,
                    "key": instance.key,
                    "created_at": instance.created_at,
                    "updated_at": instance.updated_at,
                },
            )
        else:
            logger.info("object persisted", extra={"object_name": name})

        for callback in callbacks:
            try:
                callback(instance)
            except Exception as e:
                if raise_exception:
                    raise e
                logger.exception("callback failed")

        do_heap_update()
        return instance


class UpdaterSet:
    def __init__(self, updaters: dict[str, Updater]) -> None:
        self.updaters = updaters

    def add(self, name: str, updater: Updater) -> None:
        self.updaters[name] = updater

    def update(self, name: str | None = None) -> None:
        if name:
            self.updaters[name].update()
        else:
            for updater in self.updaters.values():
                updater.update()


class SpreadUpdater(Updater):
    """
    SpreadUpdater is used to spread the update of a queryset over time (`period`).
    Each element of the queryset is updated once every `period`.
    """

    def __init__(
        self,
        name: str,
        queryset: QuerySet,
        update_func: Callable,
        period: timedelta,
    ) -> None:
        self.name = name
        self.queue_name = f"{SpreadUpdater.redis_prefix()}:queue:{name}"
        self.queryset = queryset
        self.func = update_func
        self.period = period

    def _et_key(self, k: str | UUID) -> str:
        return f"{self.redis_prefix()}:et:{k}"

    @staticmethod
    def redis_prefix() -> str:
        return f"{settings.ENV.service_name}:wise:spread_updater:"

    def update(self) -> None:
        now = timezone.now()

        r = get_redis_client()
        next_task_arr = r.lrange(self.queue_name, -1, -1)

        if next_task_arr:
            elem_key = next_task_arr[0].decode()  # type: ignore
            elem_time = iso_deserialize(r.get(self._et_key(elem_key)).decode())

            if elem_time <= now:
                elem = self.queryset.get(key=elem_key)
                self.func(elem)

                # pop queue
                if e_raw := r.rpop(self.queue_name):
                    e = e_raw.decode()  # type: ignore
                    if e != elem_key:
                        logger.error(
                            f"Schedule updater {self.name}: expected {elem_key} as head of redis queue, got {e}"
                        )
                        r.lpush(self.queue_name, e)

        else:
            count = self.queryset.all().count()
            if count == 0:
                return

            step = self.period / count
            t = now
            for elem in self.queryset.all():
                t += step
                key = str(elem.key)
                r.set(self._et_key(key), iso_serialize(t))
                r.lpush(self.queue_name, key)
