import json
import logging
from typing import Any

from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from wise.utils.periodic_tasks import (
    WiseTasks,
    _UNSUPPORTED_PERIODIC_TASK_FIELDS,
    _ALL_PERIODIC_TASK_FIELDS,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Export currently enabled PeriodicTasks"

    def handle(self, *args, **options):
        tasks = []

        for task in PeriodicTask.objects.filter(enabled=True).order_by("id"):
            if task.name == "celery.backend_cleanup":
                continue

            skip = False

            for field in _UNSUPPORTED_PERIODIC_TASK_FIELDS:
                if getattr(task, field) is not None:
                    skip = True
                    logger.warning(
                        f"Unsupported field {field} found in task {task.name}, skipping this task"
                    )
                    break
            if skip:
                continue

            task_dict = {}
            for field, default in _ALL_PERIODIC_TASK_FIELDS.items():
                value = getattr(task, field, None)
                if value == default or field in ("start_time",):
                    continue

                task_dict[field] = self._get_value(field, value)

            tasks.append(task_dict)

        result = json.dumps(tasks, indent=4)

        for wise_task, task_path in WiseTasks.as_dict().items():
            result = result.replace(f'"{task_path}"', f"WiseTasks.{wise_task}")

        print(result)

    def _get_value(self, key: str, value: Any) -> Any:
        if key == "interval":
            return self._serialize_interval_schedule(value)
        return value

    @staticmethod
    def _serialize_interval_schedule(interval: IntervalSchedule) -> str:
        unit_mapping = {
            "days": "d",
            "hours": "h",
            "minutes": "m",
            "seconds": "s",
            "microseconds": "us",
        }
        return f"{interval.every}{unit_mapping[interval.period]}"
