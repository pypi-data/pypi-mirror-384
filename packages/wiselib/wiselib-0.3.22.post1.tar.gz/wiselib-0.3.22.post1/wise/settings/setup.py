import os
import tempfile

from wise.utils.sentry import SentryHandler


def setup_settings(settings: dict) -> None:
    _install_additional_app(settings)
    _configure_project_settings(settings)
    _configure_celery_settings(settings)
    _configure_prometheus_settings(settings)
    _configure_sentry(settings)


def _install_additional_app(settings: dict) -> None:
    additional_apps = [
        "django_prometheus",
        "django_celery_results",
        "django_celery_beat",
    ]

    wise_idx = settings["INSTALLED_APPS"].index("wise")

    for app in additional_apps:
        if app not in settings["INSTALLED_APPS"]:
            settings["INSTALLED_APPS"].insert(wise_idx + 1, app)


def _configure_project_settings(settings: dict) -> None:
    if "ENV" not in settings:
        return
    env = settings["ENV"]

    if "DEBUG" not in settings:
        settings["DEBUG"] = env.debug
    if "SECRET_KEY" not in settings:
        settings["SECRET_KEY"] = env.secret_key


def _configure_celery_settings(settings: dict) -> None:
    if "ENV" not in settings:
        return
    env = settings["ENV"]

    if hasattr(env, "celery") and env.celery.enabled:
        if "CELERY_TASK_DEFAULT_QUEUE" not in settings:
            settings["CELERY_TASK_DEFAULT_QUEUE"] = (
                env.celery.default_queue
                if env.celery.default_queue
                else f"{env.service_name}-celery"
            )
        if "CELERY_RESULT_BACKEND" not in settings:
            settings["CELERY_RESULT_BACKEND"] = "django-db"
        if "CELERY_BEAT_SCHEDULER" not in settings:
            settings[
                "CELERY_BEAT_SCHEDULER"
            ] = "django_celery_beat.schedulers:DatabaseScheduler"

        if settings.get("TESTING"):
            settings["CELERY_BROKER_URL"] = "memory://"
            settings["CELERY_ALWAYS_EAGER"] = True
            settings["CELERY_TASK_EAGER_PROPAGATES"] = True

        else:
            settings["CELERY_BROKER_URL"] = env.celery.broker_url
            settings["CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP"] = True


def _get_prometheus_db_engin_wrapper(engin: str):
    engin_mapping = {
        "django.db.backends.mysql": "django_prometheus.db.backends.mysql",
        "django.db.backends.postgresql": "django_prometheus.db.backends.postgresql",
        "django.db.backends.sqlite3": "django_prometheus.db.backends.sqlite3",
        "django.contrib.gis.db.backends.postgis": "django_prometheus.db.backends"
        ".postgis",
    }
    if engin in engin_mapping:
        return engin_mapping[engin]

    return engin


def _configure_prometheus_settings(settings: dict) -> None:
    if "ENV" not in settings:
        return
    env = settings["ENV"]

    if hasattr(env, "prometheus") and env.prometheus.enabled:
        if (
            "django_prometheus.middleware.PrometheusBeforeMiddleware"
            not in settings["MIDDLEWARE"]
        ):
            settings["MIDDLEWARE"].insert(
                0, "django_prometheus.middleware.PrometheusBeforeMiddleware"
            )
        if (
            "django_prometheus.middleware.PrometheusAfterMiddleware"
            not in settings["MIDDLEWARE"]
        ):
            settings["MIDDLEWARE"].append(
                "django_prometheus.middleware.PrometheusAfterMiddleware"
            )

        for db in settings["DATABASES"].values():
            db["ENGINE"] = _get_prometheus_db_engin_wrapper(db["ENGINE"])

        coordination_dir = env.prometheus.multiproc_dir
        if not coordination_dir:
            coordination_dir = tempfile.gettempdir() + "/prometheus-multiproc-dir/"
        os.makedirs(coordination_dir, exist_ok=True)
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = coordination_dir


def _configure_sentry(settings: dict) -> None:
    if "ENV" not in settings:
        return
    env = settings["ENV"]

    if hasattr(env, "sentry"):
        SentryHandler.setup_sentry(env.sentry)
