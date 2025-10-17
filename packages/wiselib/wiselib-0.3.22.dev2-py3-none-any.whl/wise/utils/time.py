import re
from datetime import datetime, timedelta
from time import time
from typing import Tuple

try:
    from warnings import deprecated  # type: ignore
except ImportError:
    from deprecated import (
        deprecated,
    )  # TODO: remove this line after upgrading every project to python 3.13

from django.utils.timezone import make_aware

ISO_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
ISO_TIME_FORMAT_WITH_MS = "%Y-%m-%dT%H:%M:%S.%f%z"


def iso_serialize(dt: datetime, with_ms: bool = False) -> str:
    return dt.strftime(ISO_TIME_FORMAT_WITH_MS if with_ms else ISO_TIME_FORMAT)


def iso_deserialize(s: str) -> datetime:
    try:
        return datetime.strptime(s, ISO_TIME_FORMAT_WITH_MS)
    except ValueError:
        return datetime.strptime(s, ISO_TIME_FORMAT)


def expire_from_now(*, hours: int = 0, minutes: int = 0):
    return time() + hours * 3600 + minutes * 60


def get_datetime_from_timestamp_ms(ts: int, tz_aware: bool = True) -> datetime:
    dt = datetime.fromtimestamp(ts / 1000)
    return make_aware(dt) if tz_aware else dt


def get_timestamp_ms_from_datetime(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def get_datetime_from_timestamp_s(ts: int, tz_aware: bool = True) -> datetime:
    return get_datetime_from_timestamp_ms(ts * 1000, tz_aware)


def get_timestamp_s_from_datetime(dt: datetime) -> int:
    return int(dt.timestamp())


@deprecated(
    "get_datetime_from_timestamp is deprecated because of ambiguous naming, use get_datetime_from_timestamp_ms or get_datetime_from_timestamp_s instead"
)
def get_datetime_from_timestamp(ts: int, tz_aware: bool = True) -> datetime:
    return get_datetime_from_timestamp_ms(ts, tz_aware)


@deprecated(
    "get_timestamp_from_datetime is deprecated because of ambiguous naming, use get_timestamp_ms_from_datetime or get_timestamp_s_from_datetime instead"
)
def get_timestamp_from_datetime(dt: datetime) -> int:
    return get_timestamp_ms_from_datetime(dt)


def parse_duration(time_str: str) -> Tuple[int, str]:
    match = re.match(r"^\d+$", time_str)
    if match:
        return int(time_str), "seconds"

    time_str = time_str.lower()

    time_mapping = {
        "s": "seconds",
        "m": "minutes",
        "h": "hours",
        "d": "days",
        "µs": "microseconds",
        "ms": "milliseconds",
        "us": "microseconds",
    }

    match = re.match(r"^(\d+)(ms|us|µs|[smhd])$", time_str)
    if not match:
        raise ValueError("Invalid time string format")

    amount, unit = match.groups()

    amount = int(amount)

    return amount, time_mapping[unit]


def parse_timedelta(time_str: str) -> timedelta:
    amount, unit = parse_duration(time_str)
    return timedelta(**{unit: amount})
