from functools import cached_property
from typing import Callable, Optional, Any

from django.core.cache import cache
from django.db import models
from django.db.models import QuerySet, Q
from pydantic import BaseModel

from wise.utils.cache import cache_get_key
from wise.utils.redis import get_redis_client


class QuerysetHashHeap:
    def __init__(
        self,
        *,
        name: str,
        queryset: QuerySet,
        get_node_data: Callable[[Any], str],
    ):
        self.name: str = name
        self.queryset = queryset.order_by("created_at", "pk")
        self.get_node_data = get_node_data

    @cached_property
    def _heap(self) -> "HashHeap":
        heap = HashHeap(
            name=self.name,
            size=lambda: self.queryset.all().count(),
            get_node_data=lambda index: self.get_node_data(
                self.get_index_instance(index)
            ),
        )
        return heap

    def _get_instance_heap_node(self, instance: Any) -> "HashHeapNode":
        return self._heap.get_node(self._instance_index(instance))

    def _instance_index(self, instance: Any) -> int:
        return self.queryset.filter(
            Q(created_at__lt=instance.created_at)
            | Q(created_at=instance.created_at, pk__lte=instance.pk)
        ).count()

    def get_instance_heap_node_dict(self, instance: Any) -> dict | None:
        node = self._get_instance_heap_node(instance)
        return node.dict()

    def get_index_heap_node_dict(self, index: int) -> dict | None:
        return self._heap.get_node(index).dict()

    def get_index_instance(self, index: int) -> Any:
        assert index >= 1
        return self.queryset.all()[index - 1]

    def updated_recently_updated(self, timeout: int):
        r = get_redis_client()
        with r.lock(f"hash_heap:lock:{self.name}", timeout=timeout):
            params = {}

            last_updated_at = cache.get(f"hash_heap:last_updated_at:{self.name}")
            if last_updated_at:
                params["updated_at__gte"] = last_updated_at

            max_updated_at = self.queryset.aggregate(
                max_updated_at=models.Max("updated_at")
            )["max_updated_at"]
            params["updated_at__lte"] = max_updated_at

            for instance in self.queryset.filter(**params).order_by("updated_at"):
                node = self._get_instance_heap_node(instance)
                node.recalculate_with_ancestors(update_data=True)

            cache.set(f"hash_heap:last_updated_at:{self.name}", max_updated_at)

    def rebuild_heap(self, timeout: int):
        r = get_redis_client()
        with r.lock(f"hash_heap:lock:{self.name}", timeout=timeout):
            self._heap.recalculate()


class ReplicatedHashHeap:
    def __init__(
        self,
        *,
        name: str,
        get_node: Callable[[int], dict],
    ):
        self.name: str = name
        self.get_node = get_node

    def _fetch_heap_size(self) -> int:
        return int(self.get_node(0)["size"])

    def _expire_heap_size_cache(self) -> None:
        cache.delete(f"hash_heap:replicated:size:{self.name}")

    def _get_heap_size(self) -> int:
        key = f"hash_heap:replicated:size:{self.name}"
        size = cache.get(key)
        if size is None:
            size = self._fetch_heap_size()
            cache.set(key, size)
        return size

    def _get_heap_node_data(self, index: int) -> str:
        d = self.get_node(index)
        return d["data"]

    @cached_property
    def heap(self) -> "HashHeap":
        heap = HashHeap(
            name=self.name,
            size=self._get_heap_size,
            get_node_data=self._get_heap_node_data,
        )
        return heap

    def _sync_node(self, index: int) -> None:
        reference_node_data = self.get_node(index)
        node = self.heap.get_node(index)

        if node.checksum == reference_node_data["checksum"]:
            return

        if node.left_checksum != reference_node_data["left_checksum"]:
            self._sync_node(index * 2)
        if node.right_checksum != reference_node_data["right_checksum"]:
            self._sync_node(index * 2 + 1)

        node.recalculate(update_data=node.data != reference_node_data["data"])

    def sync(self, timeout: int) -> None:
        r = get_redis_client()
        with r.lock(f"hash_heap:lock:{self.name}", timeout=timeout):
            self._expire_heap_size_cache()
            self._sync_node(1)

    def update_node(self, index: int, timeout: int) -> None:
        r = get_redis_client()
        with r.lock(f"hash_heap:lock:{self.name}", timeout=timeout):
            self.heap.get_node(index).recalculate_with_ancestors(update_data=True)


class HashHeap:
    def __init__(
        self,
        name: str,
        size: int | Callable[[], int],
        get_node_data: Callable[[int], str],
    ):
        self.name = name
        self._size = size
        self.get_node_data = get_node_data

    @property
    def size(self) -> int:
        return self._size() if callable(self._size) else self._size

    def recalculate(self) -> None:
        for index in reversed(range(1, self.size + 1)):
            self.get_node(index).recalculate()

    def get_node(self, index: int) -> "HashHeapNode":
        assert 1 <= index <= self.size
        return HashHeapNode(name=self.name, index=index, heap=self)


class HashHeapNode(BaseModel):
    index: int
    heap: Any
    size: int | None = None
    data: str | None = None
    left_checksum: str | None = None
    right_checksum: str | None = None

    checksum: str | None = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.reload()

    def _get_parent(self) -> Optional["HashHeapNode"]:
        if self.index == 1:
            return None
        return self.heap.get_node(self.index // 2)

    @property
    def children(self) -> list["HashHeapNode"]:
        children = []
        for idx in (self.index * 2, self.index * 2 + 1):
            if idx < self.heap.size:
                children.append(self.heap.get_node(idx))
        return children

    def child(self, i: int) -> Optional["HashHeapNode"]:
        assert i in (0, 1), "i must be 0 or 1"
        children = self.children
        return children[i] if i < len(children) else None

    @property
    def left(self) -> Optional["HashHeapNode"]:
        return self.child(0)

    @property
    def right(self) -> Optional["HashHeapNode"]:
        return self.child(1)

    def save(self) -> None:
        """
        Save to cache
        """
        cache.set(
            f"heap_node:{self.heap.name}:{cache_get_key(self.index)}", self.dict()
        )

    def reload(self) -> None:
        """
        Re-fetch from cache (and save it to cache)
        """
        data = cache.get(f"heap_node:{self.heap.name}:{cache_get_key(self.index)}")
        if data:
            self.size = data["size"]
            self.checksum = data["checksum"]
        self.save()

    def recalculate(self, update_data: bool = False) -> None:
        self.reload()

        self.size = self.calculate_size()
        if update_data:
            self._update_data()
        self.checksum = self.calculate_checksum()

        self.save()

    def recalculate_with_ancestors(self, update_data: bool = False) -> None:
        self.recalculate(update_data=update_data)
        parent = self._get_parent()
        if parent:
            parent.recalculate_with_ancestors()

    def calculate_size(
        self,
    ) -> int:
        size = 1
        for child in self.children:
            if child.size is None:
                child.recalculate()
            assert child.size is not None
            size += child.size
        return size

    def _update_data(self) -> None:
        self.data = self.heap.get_node_data(self.index)

    def calculate_checksum(self) -> str:
        if not self.data:
            self._update_data()

        left, right = self.left, self.right
        if left:
            left.reload()
        if right:
            right.reload()

        self.left_checksum = left.checksum if left else None
        self.right_checksum = right.checksum if right else None

        if left is not None and self.left_checksum is None:
            left.recalculate()
            self.left_checksum = left.checksum

        if right is not None and self.right_checksum is None:
            right.recalculate()
            self.right_checksum = right.checksum

        return cache_get_key(
            "hash_heap_node_checksum",
            index=self.index,
            size=self.size,
            data=self.data,
            left=self.left_checksum,
            right=self.right_checksum,
        )
