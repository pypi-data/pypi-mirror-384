from unittest.mock import MagicMock
from time import perf_counter as time_now

import redis
import redis.lock
from django.conf import settings

from wise.utils.exception import NotLockedError
from wise.utils.monitoring import REDIS_COMMAND_DURATION

_redis_client = None


class RedisClientWithMonitoring(redis.Redis):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run_command(self, command: str, *args, **kwargs):
        start = time_now()
        success = "false"
        try:
            ret = getattr(super(), command)(*args, **kwargs)
            success = "true"
            return ret
        finally:
            REDIS_COMMAND_DURATION.labels(command, success).observe(time_now() - start)

    def append(self, *args, **kwargs):
        return self.run_command("append", *args, **kwargs)

    def bitcount(self, *args, **kwargs):
        return self.run_command("bitcount", *args, **kwargs)

    def bitfield(self, *args, **kwargs):
        return self.run_command("bitfield", *args, **kwargs)

    def bitfield_ro(self, *args, **kwargs):
        return self.run_command("bitfield_ro", *args, **kwargs)

    def bitop(self, *args, **kwargs):
        return self.run_command("bitop", *args, **kwargs)

    def bitpos(self, *args, **kwargs):
        return self.run_command("bitpos", *args, **kwargs)

    def copy(self, *args, **kwargs):
        return self.run_command("copy", *args, **kwargs)

    def decrby(self, *args, **kwargs):
        return self.run_command("decrby", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.run_command("delete", *args, **kwargs)

    def dump(self, *args, **kwargs):
        return self.run_command("dump", *args, **kwargs)

    def exists(self, *args, **kwargs):
        return self.run_command("exists", *args, **kwargs)

    def expire(self, *args, **kwargs):
        return self.run_command("expire", *args, **kwargs)

    def expireat(self, *args, **kwargs):
        return self.run_command("expireat", *args, **kwargs)

    def expiretime(self, *args, **kwargs):
        return self.run_command("expiretime", *args, **kwargs)

    def get(self, *args, **kwargs):
        return self.run_command("get", *args, **kwargs)

    def getdel(self, *args, **kwargs):
        return self.run_command("getdel", *args, **kwargs)

    def getex(self, *args, **kwargs):
        return self.run_command("getex", *args, **kwargs)

    def getbit(self, *args, **kwargs):
        return self.run_command("getbit", *args, **kwargs)

    def getrange(self, *args, **kwargs):
        return self.run_command("getrange", *args, **kwargs)

    def getset(self, *args, **kwargs):
        return self.run_command("getset", *args, **kwargs)

    def incrby(self, *args, **kwargs):
        return self.run_command("incrby", *args, **kwargs)

    def incrbyfloat(self, *args, **kwargs):
        return self.run_command("incrbyfloat", *args, **kwargs)

    def keys(self, *args, **kwargs):
        return self.run_command("keys", *args, **kwargs)

    def lmove(self, *args, **kwargs):
        return self.run_command("lmove", *args, **kwargs)

    def blmove(self, *args, **kwargs):
        return self.run_command("blmove", *args, **kwargs)

    def mget(self, *args, **kwargs):
        return self.run_command("mget", *args, **kwargs)

    def mset(self, *args, **kwargs):
        return self.run_command("mset", *args, **kwargs)

    def msetnx(self, *args, **kwargs):
        return self.run_command("msetnx", *args, **kwargs)

    def move(self, *args, **kwargs):
        return self.run_command("move", *args, **kwargs)

    def persist(self, *args, **kwargs):
        return self.run_command("persist", *args, **kwargs)

    def pexpire(self, *args, **kwargs):
        return self.run_command("pexpire", *args, **kwargs)

    def pexpireat(self, *args, **kwargs):
        return self.run_command("pexpireat", *args, **kwargs)

    def pexpiretime(self, *args, **kwargs):
        return self.run_command("pexpiretime", *args, **kwargs)

    def psetex(self, *args, **kwargs):
        return self.run_command("psetex", *args, **kwargs)

    def pttl(self, *args, **kwargs):
        return self.run_command("pttl", *args, **kwargs)

    def hrandfield(self, *args, **kwargs):
        return self.run_command("hrandfield", *args, **kwargs)

    def randomkey(self, *args, **kwargs):
        return self.run_command("randomkey", *args, **kwargs)

    def rename(self, *args, **kwargs):
        return self.run_command("rename", *args, **kwargs)

    def renamenx(self, *args, **kwargs):
        return self.run_command("renamenx", *args, **kwargs)

    def restore(self, *args, **kwargs):
        return self.run_command("restore", *args, **kwargs)

    def set(self, *args, **kwargs):
        return self.run_command("set", *args, **kwargs)

    def setbit(self, *args, **kwargs):
        return self.run_command("setbit", *args, **kwargs)

    def setex(self, *args, **kwargs):
        return self.run_command("setex", *args, **kwargs)

    def setnx(self, *args, **kwargs):
        return self.run_command("setnx", *args, **kwargs)

    def setrange(self, *args, **kwargs):
        return self.run_command("setrange", *args, **kwargs)

    def stralgo(self, *args, **kwargs):
        return self.run_command("stralgo", *args, **kwargs)

    def strlen(self, *args, **kwargs):
        return self.run_command("strlen", *args, **kwargs)

    def substr(self, *args, **kwargs):
        return self.run_command("substr", *args, **kwargs)

    def touch(self, *args, **kwargs):
        return self.run_command("touch", *args, **kwargs)

    def ttl(self, *args, **kwargs):
        return self.run_command("ttl", *args, **kwargs)

    def type(self, *args, **kwargs):
        return self.run_command("type", *args, **kwargs)

    def watch(self, *args, **kwargs):
        return self.run_command("watch", *args, **kwargs)

    def unwatch(self, *args, **kwargs):
        return self.run_command("unwatch", *args, **kwargs)

    def unlink(self, *args, **kwargs):
        return self.run_command("unlink", *args, **kwargs)

    def lcs(self, *args, **kwargs):
        return self.run_command("lcs", *args, **kwargs)


def get_redis_client() -> RedisClientWithMonitoring:
    global _redis_client

    if _redis_client:
        return _redis_client

    redis_settings = settings.ENV.redis
    _redis_client = RedisClientWithMonitoring(
        host=redis_settings.host,
        port=redis_settings.port,
        db=redis_settings.db,
        username=redis_settings.user,
        password=redis_settings.password,
    )
    return _redis_client


def ensure_locked(lock: redis.lock.Lock) -> None:
    if lock.acquire(blocking=False):
        lock.release()
        raise NotLockedError()


def get_mock_redis():
    r = MagicMock()
    r.get = lambda *args, **kwargs: None
    return r
