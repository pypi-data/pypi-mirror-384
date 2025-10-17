import hashlib
import json
from datetime import timedelta
from typing import Callable, Optional, Union, Any

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.serializers import SerializerMetaclass

from wise.station.consts import HEAP_UPDATE_TIMEOUT
from wise.station.heap import QuerysetHashHeap
from wise.utils.redis import get_redis_client

Duration = Union[int, float, timedelta]

RECENTLY_UPDATED_THRESHOLD = timedelta(minutes=15)
CACHE_EXPIRATION = timedelta(days=1)


class Publisher:
    def __init__(
        self,
        *,
        name: str | None = None,
        queryset: QuerySet,
        serializer: SerializerMetaclass | Callable | None = None,
        publish_to_broker: Optional[Callable[[str, dict], None]] = None,
        publish: Optional[Callable] = None,
        checksum: Optional[Callable] = None,
        recently_updated_threshold: Duration = RECENTLY_UPDATED_THRESHOLD,
        cache_expiration: Duration | None = CACHE_EXPIRATION,
        enable_publish_all: bool = True,
        enable_heap: bool = False,
    ):
        self._publish: Optional[Callable] = publish
        self.name: str | None = name
        self.queryset = queryset
        self.serializer: SerializerMetaclass | Callable | None = serializer
        self.publish_to_broker: Optional[Callable] = publish_to_broker
        self.checksum: Optional[Callable] = checksum
        self.recently_updated_threshold: Duration = recently_updated_threshold
        self.cache_expiration: Duration | None = cache_expiration
        self.enable_heap: bool = enable_heap
        self.enable_publish_all = enable_publish_all
        self._heap: QuerysetHashHeap | None = None

        if not publish:
            assert name, "name is required"
            assert serializer is not None, "serializer is required"
            assert publish_to_broker, "publish_to_broker is required"

    def publish(self, instance, *args, force: bool = False, **kwargs):
        if self._publish:
            self._publish(instance, *args, **kwargs)
            return

        if getattr(settings, "TESTING", False):
            return

        assert self.name
        assert self.serializer
        assert self.publish_to_broker

        r = get_redis_client()

        object_key = str(instance.key)

        with r.lock(f"publisher_lock:{self.name}:{object_key}", timeout=10):
            hash_key = f"publisher_last_msg:{self.name}:{object_key}"
            checksum = self.get_checksum(instance)

            if not force and r.get(hash_key) == checksum:
                return

            if heap := self.heap:
                heap.updated_recently_updated(HEAP_UPDATE_TIMEOUT)

            self.publish_to_broker(object_key, self.get_instance_message(instance))
            r.set(
                hash_key,
                checksum,
                ex=(
                    int(_duration_to_seconds(self.cache_expiration))
                    if self.cache_expiration
                    else None
                ),
            )

    def get_instance_message(self, instance: Any) -> dict:
        assert self.name
        assert self.serializer

        if isinstance(self.serializer, SerializerMetaclass):
            data = self.serializer(instance).data
        else:
            data = self.serializer(instance)

        data = json.loads(
            json.dumps(data, cls=DjangoJSONEncoder)
        )  # To convert OrderedDicts/Pydantic objects to simple dicts.
        d = {
            "object_name": self.name,
            "body": data,
        }

        if self.enable_heap:
            heap = self.heap
            assert heap
            if heap_data := heap.get_instance_heap_node_dict(instance):
                d["heap_node"] = heap_data

        return d

    def get_heap_index_message(self, index: int) -> dict:
        heap = self.heap
        assert heap
        instance = heap.get_index_instance(index)
        assert instance
        return self.get_instance_message(instance)

    def get_checksum(self, instance):
        if self.checksum:
            return self.checksum(instance)
        return (
            hashlib.sha256(
                json.dumps(
                    self.get_instance_message(instance), cls=DjangoJSONEncoder
                ).encode()
            )
            .hexdigest()
            .encode()
        )

    def _publish_queryset(self, queryset: QuerySet, *args, **kwargs):
        for instance in queryset.all():
            self.publish(instance, *args, **kwargs)

    def publish_all(self, *args, **kwargs):
        if self.enable_publish_all:
            self._publish_queryset(self.queryset, *args, **kwargs)

    def publish_recently_updated(
        self, threshold: Duration | None = None, *args, **kwargs
    ):
        if threshold is None:
            threshold = self.recently_updated_threshold
        delta = _duration_to_timedelta(threshold)
        self._publish_queryset(
            self.queryset.filter(updated_at__gte=timezone.now() - delta),
            *args,
            **kwargs,
        )

    def get_heap_node_data(self, instance: Any) -> str:
        if self.checksum:
            d = self.checksum(instance)
            if isinstance(d, str):
                d = d.encode()
        else:
            d = json.dumps(
                self.get_instance_message(instance), cls=DjangoJSONEncoder
            ).encode()

        return hashlib.sha256(d).hexdigest()

    @property
    def heap(self) -> QuerysetHashHeap | None:
        if not self.enable_heap:
            return None
        assert self.name

        if self._heap is not None:
            return self._heap

        self._heap = QuerysetHashHeap(
            name=self.name,
            queryset=self.queryset,
            get_node_data=self.get_heap_node_data,
        )
        return self._heap


def _duration_to_seconds(d: Duration) -> float:
    if isinstance(d, timedelta):
        return d.total_seconds()
    return float(d)


def _duration_to_timedelta(d: Duration) -> timedelta:
    if isinstance(d, timedelta):
        return d
    return timedelta(seconds=d)
