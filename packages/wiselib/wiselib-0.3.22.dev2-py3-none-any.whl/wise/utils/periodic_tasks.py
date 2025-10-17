import logging
from typing import Any

from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

from wise.utils.django import get_environment
from wise.utils.time import parse_duration

logger = logging.getLogger(__name__)


def set_periodic_tasks(data: dict | list, disable_rest: bool = True) -> None:
    if isinstance(data, list):
        tasks = data
    else:
        env = get_environment()
        if env is None:
            logger.error("Environment not set. Please set settings.ENV.environment")
            return
        if env not in data:
            return
        tasks = data[env]

    task_names = {"celery.backend_cleanup"}
    for task in tasks:
        if "name" not in task:
            logger.error("Periodic task is missing 'name' field")
            continue
        if task["name"] in task_names:
            logger.error(f"Duplicate periodic task name: {task['name']}")
            continue
        task_names.add(task["name"])

        _save_periodic_task(task)

    if disable_rest:
        _disable_remaining_periodic_tasks(task_names)


class WiseTasks:
    PUBLISH_EVERYTHING = "wise.tasks.publish_everything"
    PUBLISH_RECENTLY_UPDATED_OBJECTS = "wise.tasks.publish_recently_updated_objects"
    UPDATE_EVERYTHING = "wise.tasks.update_everything"
    UPDATE_SET = "wise.tasks.update_set"
    REBUILD_PUBLISHER_HEAPS = "wise.tasks.rebuild_publisher_heaps"
    UPDATE_PUBLISHER_HEAPS = "wise.tasks.update_publisher_heaps"
    SYNC_UPDATER_HEAPS = "wise.tasks.sync_updater_heaps"

    @classmethod
    def all(cls) -> list[str]:
        res = []
        for attr_name, attr_value in cls.__dict__.items():
            if not attr_name.startswith("__") and isinstance(attr_value, str):
                res.append(attr_value)
        return res

    @classmethod
    def as_dict(cls) -> dict[str, str]:
        res = {}
        for attr_name, attr_value in cls.__dict__.items():
            if not attr_name.startswith("__") and isinstance(attr_value, str):
                res[attr_name] = attr_value
        return res


_UNSUPPORTED_PERIODIC_TASK_FIELDS = ("crontab", "solar", "clocked")
_ALL_PERIODIC_TASK_FIELDS = {
    "name": None,
    "task": None,
    "interval": None,
    "crontab": None,
    "solar": None,
    "clocked": None,
    "args": "[]",
    "kwargs": "{}",
    "queue": None,
    "exchange": None,
    "routing_key": None,
    "headers": "{}",
    "priority": None,
    "expires": None,
    "expire_seconds": None,
    "one_off": False,
    "start_time": None,
    "enabled": True,
    "description": "",
}


def _save_periodic_task(task_dict: dict) -> None:
    try:
        task = PeriodicTask.objects.get(name=task_dict["name"])
        changed = False
    except PeriodicTask.DoesNotExist:
        task = PeriodicTask(name=task_dict["name"])
        changed = True

    defaults = _ALL_PERIODIC_TASK_FIELDS | {"start_time": timezone.now()}

    for key, value in task_dict.items():
        setattr(task, key, _get_periodic_task_value(key, value))

    if "enabled" not in task_dict:  # enable task unless explicitly disabled
        task.enabled = True

    for key, value in defaults.items():
        if getattr(task, key, None) is None:
            setattr(task, key, value)

    if not changed:
        original_task = PeriodicTask.objects.get(name=task.name)
        for key in _ALL_PERIODIC_TASK_FIELDS:
            if getattr(original_task, key, None) != getattr(task, key, None):
                changed = True
                break

    if changed:
        logger.info(f"Saving periodic task: {task.name}")
        task.save()


def _get_periodic_task_value(key: str, value: Any) -> Any:
    if key == "crontab":
        return _crontab_schedule(value)
    if key == "interval":
        return _interval_schedule(value)
    if key in _UNSUPPORTED_PERIODIC_TASK_FIELDS:
        raise NotImplementedError(
            f"PeriodicTask with {key} is not supported yet. "
            f"Contact wise owners or implement it yourself and send us a Pull Request ;)"
        )
    return value


def _disable_remaining_periodic_tasks(task_names: set | list) -> None:
    for task in list(
        PeriodicTask.objects.filter(enabled=True).exclude(name__in=task_names)
    ):
        logger.info(f"Disabling unknown periodic task: {task.name}")
        task.enabled = False
        task.save()


def _interval_schedule(duration: str) -> IntervalSchedule:
    amount, unit = parse_duration(duration)
    if unit == "milliseconds":
        unit = "microseconds"
        amount *= 1000

    return IntervalSchedule.objects.get_or_create(every=amount, period=unit)[0]


def _crontab_schedule(crontab: str) -> CrontabSchedule:
    minute, hour, day_of_month, month_of_year, day_of_week = crontab.split()[:5]

    return CrontabSchedule.objects.get_or_create(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
    )[0]
