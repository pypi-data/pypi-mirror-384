import logging
from prometheus_client import Counter

from wise.utils.monitoring import REGISTRY, METRICS_NAMESPACE

_LOG_LEVEL_TOTAL = Counter(
    "django_log_level_count",
    "Counts of logs by level",
    ["level"],
    registry=REGISTRY,
    namespace=METRICS_NAMESPACE,
)


class PrometheusLogHandler(logging.Handler):
    def emit(self, record):
        _LOG_LEVEL_TOTAL.labels(level=record.levelname.lower()).inc()
