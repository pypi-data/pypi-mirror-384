from functools import wraps
from time import perf_counter as time_now
from typing import Callable

from django.conf import settings
from prometheus_client import Counter, Histogram, Summary, multiprocess

from prometheus_client.registry import CollectorRegistry


__all__ = [
    "REGISTRY",
    "DURATION_SECONDS_BUCKETS",
    "METRICS_NAMESPACE",
    "Observer",
    "observe",
    "REDIS_COMMAND_DURATION",
    "KAFKA_CONSUME_DURATION",
    "KAFKA_PRODUCE_DURATION",
    "HTTP_CLIENT_DURATION",
]

REGISTRY = CollectorRegistry()
multiprocess.MultiProcessCollector(REGISTRY)

METRICS_NAMESPACE = settings.ENV.prometheus.prefix

DURATION_SECONDS_BUCKETS = (
    0.05,
    0.1,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
    7.5,
    10.0,
    15.0,
    20.0,
    30.0,
    60.0,
    120.0,
    float("inf"),
)

DEPENDENCY_DURATION_SECONDS_BUCKETS = (
    0.005,
    0.01,
    0.05,
    0.075,
    0.1,
    0.25,
    0.5,
    0.75,
    1.0,
    1.5,
    2.0,
    3.0,
    6.0,
    12.0,
    float("inf"),
)


class Observer:
    def __init__(self, name: str, const_labels: dict | None = None) -> None:
        self.name = name
        self.const_labels = const_labels if const_labels else {}
        self.start: float | None = None

    @property
    def _labels(self) -> dict:
        return _get_observer_labels(self.name, self.const_labels)

    def set_labels(self, const_labels: dict) -> None:
        self.const_labels = const_labels

    def add_labels(self, const_labels: dict) -> None:
        self.const_labels.update(const_labels)

    def __enter__(self):
        _OBSERVER_ATTEMPTS_TOTAL.labels(**self._labels).inc()
        self.start = time_now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.start
        success = "true" if not exc_type else "false"
        labels = self._labels
        if not labels.get("success"):
            labels["success"] = success

        _OBSERVER_TOTAL.labels(**self._labels).inc()
        _OBSERVER_DURATION.labels(**self._labels).observe(time_now() - self.start)


def observe(name: str, const_labels: dict | None = None) -> Callable:
    labels = _get_observer_labels(name, const_labels)

    def func(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            _OBSERVER_ATTEMPTS_TOTAL.labels(**labels).inc()
            start = time_now()
            success = "false"
            try:
                res = f(*args, **kwargs)
                success = "true"
                return res
            finally:
                if not labels.get("success"):
                    labels["success"] = success
                _OBSERVER_TOTAL.labels(**labels).inc()
                _OBSERVER_DURATION.labels(**labels).observe(time_now() - start)

        return wrapped

    return func


_OBSERVER_NAME_LABEL = "observer_name"

_OBSERVER_CONST_LABEL_NAMES = [
    "observer_type",
    "success",
    "method",
    "status",
    "api_endpoint",
    "api_name",
]

if hasattr(settings, "OBSERVER_EXTRA_LABEL_NAMES"):
    _OBSERVER_CONST_LABEL_NAMES.extend(getattr(settings, "OBSERVER_EXTRA_LABEL_NAMES"))
    _OBSERVER_CONST_LABEL_NAMES = list(set(_OBSERVER_CONST_LABEL_NAMES))


_OBSERVER_ATTEMPTS_TOTAL = Counter(
    f"observer_attempts_count_total",
    f"Observer attempts total count",
    registry=REGISTRY,
    labelnames=[*_OBSERVER_CONST_LABEL_NAMES, _OBSERVER_NAME_LABEL],
)  # type: ignore

_OBSERVER_TOTAL = Counter(
    f"observer_count_total",
    f"Observer total count",
    registry=REGISTRY,
    labelnames=[*_OBSERVER_CONST_LABEL_NAMES, _OBSERVER_NAME_LABEL],
)  # type: ignore

_OBSERVER_DURATION = Histogram(
    f"observer_duration_seconds",
    f"Observer duration (seconds)",
    registry=REGISTRY,
    buckets=DURATION_SECONDS_BUCKETS,
    labelnames=[*_OBSERVER_CONST_LABEL_NAMES, _OBSERVER_NAME_LABEL],
)  # type: ignore

REDIS_COMMAND_DURATION = Histogram(
    f"redis_duration_seconds",
    f"Redis duration (seconds)",
    buckets=DEPENDENCY_DURATION_SECONDS_BUCKETS,
    registry=REGISTRY,
    labelnames=["command", "status"],
)

KAFKA_CONSUME_DURATION = Histogram(
    f"kafka_consume_duration_seconds",
    f"Kafka consume duration (seconds)",
    buckets=DEPENDENCY_DURATION_SECONDS_BUCKETS,
    registry=REGISTRY,
    labelnames=["topic", "status"],
)

KAFKA_PRODUCE_DURATION = Histogram(
    f"kafka_produce_duration_seconds",
    f"Kafka produce duration (seconds)",
    buckets=DEPENDENCY_DURATION_SECONDS_BUCKETS,
    registry=REGISTRY,
    labelnames=["topic", "status"],
)

HTTP_CLIENT_DURATION = Histogram(
    f"http_client_duration_seconds",
    f"HTTP client duration (seconds)",
    buckets=DEPENDENCY_DURATION_SECONDS_BUCKETS,
    registry=REGISTRY,
    labelnames=["service_name", "api_name", "method", "status"],
)


def _get_observer_labels(observer_name: str, const_labels: dict | None) -> dict:
    labels = {_OBSERVER_NAME_LABEL: observer_name}
    if const_labels:
        labels.update(const_labels)

    for k in _OBSERVER_CONST_LABEL_NAMES:
        labels.setdefault(k, "")
    return labels
