from typing import Any


def getpath(o: Any, path: str, default=None) -> Any:
    for p in path.split("."):
        if o is None:
            return default
        o = getattr(o, p, None)
    return default if o is None else o
