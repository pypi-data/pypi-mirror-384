from django.conf import settings
from .python import getpath


def is_testing() -> bool:
    return getattr(settings, "TESTING", False)


def get_environment() -> str | None:
    if e := getpath(settings, "ENV.environment"):
        return e
    return getpath(settings, "ENV.sentry.environment")
