from datetime import timedelta
from logging import getLogger

from wise.utils.cache import cache_get_key
from wise.utils.redis import get_redis_client


logger = getLogger(__name__)


def rate_limit_func(period: int | timedelta | None = None):  # period is in seconds
    def decorator(func):
        def wrapper(*args, **kwargs):
            final_period = period
            if final_period is None:
                final_period = kwargs.pop("rate_limit_period")

            if final_period is None:
                logger.error("rate_limit_period is not set")

            r = get_redis_client()
            cache_key = (
                "_wise:rate_limit:"
                + func.__name__
                + ":"
                + cache_get_key(*args, **kwargs)
            )
            if r.get(cache_key):
                return
            result = func(*args, **kwargs)
            if final_period:
                r.set(cache_key, 1, ex=final_period)
            else:
                r.set(cache_key, 1, ex=60 * 60 * 24)
            return result

        return wrapper

    return decorator
