from typing import Iterable

from wise.station.registry import station_registry
from wise.utils.celery import app
from wise.utils.monitoring import observe
from wise.station.consts import (
    HEAP_SYNC_TIMEOUT,
    HEAP_UPDATE_TIMEOUT,
    HEAP_REBUILD_TIMEOUT,
)
from wise.station.heap import QuerysetHashHeap, ReplicatedHashHeap


@app.task
@observe("publish_everything", const_labels={"observer_type": "celery_task"})
def publish_everything() -> None:
    for publisher in station_registry.publishers:
        publisher.publish_all()


@app.task
@observe(
    "publish_recently_updated_objects", const_labels={"observer_type": "celery_task"}
)
def publish_recently_updated_objects() -> None:
    for publisher in station_registry.publishers:
        publisher.publish_recently_updated()


@app.task
@observe("update_everything", const_labels={"observer_type": "celery_task"})
def update_everything() -> None:
    if station_registry.periodic_updaters is None:
        return
    station_registry.periodic_updaters.update("all")


@app.task
@observe("update_set", const_labels={"observer_type": "celery_task"})
def update_set(name: str) -> None:
    if station_registry.periodic_updaters is None:
        return
    station_registry.periodic_updaters.update(name)


@app.task
def rebuild_publisher_heaps(timeout: int | None = None) -> None:
    for heap in _get_publisher_heaps():
        heap.rebuild_heap(timeout or HEAP_REBUILD_TIMEOUT)


@app.task
def update_publisher_heaps(timeout: int | None = None) -> None:
    for heap in _get_publisher_heaps():
        heap.updated_recently_updated(timeout or HEAP_UPDATE_TIMEOUT)


def _get_publisher_heaps() -> Iterable[QuerysetHashHeap]:
    for publisher in station_registry.publishers:
        if publisher.enable_heap:
            heap = publisher.heap
            if heap is None:
                continue
            yield heap


@app.task
def sync_updater_heaps(timeout: int | None = None) -> None:
    for updater in _get_updater_heaps():
        updater.sync(timeout or HEAP_SYNC_TIMEOUT)


def _get_updater_heaps() -> Iterable[ReplicatedHashHeap]:
    for updater in station_registry.updater_handlers:
        for heap in updater.get_heaps():
            yield heap
