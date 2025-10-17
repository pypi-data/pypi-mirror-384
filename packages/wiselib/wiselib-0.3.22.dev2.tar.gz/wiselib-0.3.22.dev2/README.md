# Wise

Wise is meant to be used as a core for Wisdomise Python/Django microservices.

## Installation

```bash
poetry add wiselib
```

## Usage

### Installation and configuration

Add to installed apps in your Django settings:

```python
INSTALLED_APPS = [
    ...
    'wise',
    ...
]
```

You can remove the following apps from INSTALLED_APPS (wise will add them):

```python
INSTALLED_APPS = [
    ...
    # "django_prometheus",
    # "django_celery_results",
    # "django_celery_beat",
    ...
]
```

Add to settings.py:

```python
from wise.settings import setup_settings
...
setup_settings(globals())
```

Also you don't need to set the following variables in settings.py,
wise will set them for you:

```python
# CELERY_BROKER_URL = ...
# CELERY_RESULT_BACKEND = ...
# CELERY_BEAT_SCHEDULER = ...
# Prometheus settings...
# SentryHandler.setup_sentry(ENV.sentry) # Sentry settings...
```

Setup env.py:

```python
from functools import lru_cache

from dotenv import find_dotenv, load_dotenv
from pydantic import StrictStr
from pydantic_settings import SettingsConfigDict
from wise.settings.env import (
    EnvSettings as BaseEnvSettings,
    SentrySettings,
    PostgresSettings,
    RedisSettings,
    CelerySettings,
    KafkaSettings,
    PrometheusSettings,
    TracingSettings,
)

load_dotenv()


class EnvSettings(BaseEnvSettings):
    service_name: StrictStr = "wise"

    sentry: SentrySettings
    postgres: PostgresSettings
    kafka: KafkaSettings
    redis: RedisSettings
    celery: CelerySettings
    prometheus: PrometheusSettings
    tracing: TracingSettings

    model_config = SettingsConfigDict(
        env_prefix="WISE_",
        env_nested_delimiter="__",
        env_file=find_dotenv(raise_error_if_not_found=False),
        extra="allow",  # Ignore extra fields
    )


@lru_cache
def get_env_settings() -> EnvSettings:
    return EnvSettings()  # type: ignore
```

### Utilities

#### Models

You don't need the `BaseModel` definition in your code. Use this instead:

```python
from wise.utils.models import BaseModel
```

#### Station

Create an app in your project named `station` (if it doesn't exist)
and add it to `INSTALLED_APPS` in your Django settings.

Create the following files:

```python
# my_project/station/publishers.py
from wise.station.publish import Publisher

# All publishers

publishers: list[Publisher] = [
    ...
] # can be empty
```

```python
# my_project/station/updaters.py
from django.conf import settings
from wise.station.updater import UpdaterHandler

handle_temple_station_message = UpdaterHandler().add("asset", AssetUpdater) # this is an exmple


kafka_updater_handlers = {
    settings.ENV.kafka.temple_station_topic_name: handle_temple_station_message,
} # dict[topic_name, UpdaterHandler]

all_updater_handlers = list(kafka_updater_handlers.values()) # list[UpdaterHandler], can be empty

periodic_updaters = [
    ...
] # can be empty
```

```python
# my_project/station/setup.py (copy this file as a whole)
from wise.station.registry import station_registry

from station.publishers import publishers
from station.updaters import kafka_updater_handlers, all_updater_handlers, periodic_updaters
from station.periodic_tasks import periodic_tasks


def setup():
   station_registry.set_publishers(publishers)
   station_registry.set_kafka_updater_handlers(kafka_updater_handlers)
   station_registry.set_updater_handlers(all_updater_handlers)
   station_registry.set_periodic_updaters(periodic_updaters)
   station_registry.set_periodic_tasks(periodic_tasks)
```

```python
# my_project/station/apps.py (copy this file as a whole)
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class StationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "station"

    def ready(self):
        from station.setup import setup

        setup()
```

You should also remove any `Updater, Publisher, ModelUpdater, SkipUpdate, etc.` definitions from your project and import them from `wise.station`.

#### Monitoring

You don't need the `monitoring.py` in your projects.
Use this instead:

```python
from wise.utils.monitoring import Observer, observe, REGISTRY, METRICS_NAMESPACE
```

You also don't need the command `serve_metrics` in your projects. Wise will take care of it.

#### Celery

You don't need the `celery.py` in your projects.
Use this instead:

```python
from wise.utils.celery import app

@app.task
def my_task():
    ...
```


#### Periodic Tasks

You can set the celery periodic tasks deterministically from your code instead of using the admin panel.
You need to do this in `station/setup.py`:

```python
# my_project/station/setup.py (copy this file as a whole)
from wise.station.registry import station_registry

from station.periodic_tasks import periodic_tasks


def setup():
   ...
   station_registry.set_periodic_tasks(periodic_tasks)
```

Also add this to your stat up script/entrypoint after `manage.py migrate`:
```shell
python3 manage.py wise_setup
```

The argument passed to `set_periodic_tasks` should either be a list of tasks (which will be used for all environments),
or a dictionary with environment names (production/staging) as keys and lists of tasks as values.

Each task should be a dictionary. See the examples:

```python
from wise.station.registry import station_registry

station_registry.set_periodic_tasks(
   [
      {
         "name": "My Task",  # should be unique, and should not be changed later, as it's used as identifier
         "task": "my_project.tasks.my_task",  # task function path
         "interval": "10m",  # every 10 minutes. Should be a string. Valid examples: '1s', '2m', '3h', '4d', '5ms', '30' (30 seconds), '6us' or '6µs' (microseconds, both are valid)
         "args": "[1, 2, 3]",  # optional
         "enabled": False,  # optional, will be set to True each time 'set_periodic_tasks' is called, if not provided
      }
    ]
)
```

You can also set the periodic tasks for different environments:

```python
from wise.station.registry import station_registry

station_registry.set_periodic_tasks(
   {
      "production": [
         {
            "name": "My Task",
            "task": "my_project.tasks.my_task",
            "interval": "1m",
         }
      ],
      "staging": [
         {
            "name": "My Task",
            "task": "my_project.tasks.my_task",
            "interval": "10m",
         }
      ],
   }
)
```

All other intervaled periodic tasks will be disabled each time `set_periodic_tasks` is called. You can avoid this by
passing `disable_rest=False` to `set_periodic_tasks`.

For the sake of simplicity and backward compatibility (in case of future updates), you can use `WiseTasks` to refer to Wise tasks:

```python
from wise.station.registry import station_registry
from wise.utils.periodic_tasks import WiseTasks

...
station_registry.set_periodic_tasks(
   {
      "production": [
         {
            "name": "Wise: Publish Everything",
            "task": WiseTasks.PUBLISH_EVERYTHING,
            "interval": "1m",
         }
      ],
   }  # note that since "staging" is omitted, this will not impact the staging environment at all
)
```

**You can use `manage.py export_periodic_tasks` to export the currently enabled periodic tasks to avoid manual entry.**

All valid periodic task fields that you can use in your task definition are:

```python3
[
    "name",
    "task",
    "interval",
    "crontab",
    "solar",
    "clocked",
    "args",
    "kwargs",
    "queue",
    "exchange",
    "routing_key",
    "headers",
    "priority",
    "expires",
    "expire_seconds",
    "one_off",
    "start_time",
    "enabled",
    "description"
]
```

See the [Django Celery Beat documentation](https://django-celery-beat.readthedocs.io/en/latest/reference/django-celery-beat.models.html#django_celery_beat.models.PeriodicTask) for more information.

#### Tracing

You don't need the `tracing.py` in your projects.
Use this instead:

```python
from wise.utils.tracing import with_trace, trader
```

#### Views & URLs

You don't need health check view in your project anymore. Wise will take care of it.

Add wise urls to your urls.py:

```python
urlpatterns = [
    ...,
    path("", include("wise.urls")),
]
```

#### Redis

You don't need the `redis.py` in your projects. Use this instead:

```python
from wise.utils.redis import get_redis_client
from wise.utils.redis import get_mock_redis # for testing
```

#### Kafka

You don't need to define Kafka Producer in your projects. Use this instead:

```python
# my_project/utils/kafka.py
from django.conf import settings
from wise.utils.kafka import KafkaProducer

station_kafka_producer = KafkaProducer(settings.ENV.kafka.my_project_station_topic_name)
```

```python
# my_project/some_file.py
from my_project.utils.kafka import station_kafka_producer
station_kafka_producer.produce("my message")
```

You also don't need consume.py (`consume` management command) anymore. Wise will take care of it.

#### Caching

You don't need to implement `cache_for` and `cache_get_key` in your projects. Remove them and import from wise.

```python
from wise.utils.cache import cache_for, cache_get_key
```

#### Time

The time module consists of some useful functions for working with time.

```python
from wise.utils.time import ISO_TIME_FORMAT, iso_serialize, iso_deserialize, expire_from_now
from wise.utils.time import get_datetime_from_timestamp, get_timestamp_from_datetime, parse_timedelta
```

#### Numbers

The numbers module consists of some useful functions for working with numbers.

```python
from wise.utils.numbers import is_zero, safe_add, safe_sub, safe_div, safe_mult, safe_sum, safe_abs, safe_prod
from wise.utils.numbers import safe_abs, safe_eq, safe_gt, safe_gte, safe_lt, safe_lte, safe_max, safe_min

is_zero(1e-12) # True

safe_add(1.1, 2.2) # uses Decimal to avoid floating point errors. all safe_* functions do.
```

#### Rate Limit

There is a `rate_limit_func` decorator you can use to limit the number of calls to a function. (otherwise returns None).

It uses the `args` and `kwargs` in your function call (so it's per-parameter, not per-function).
Your function parameters should be cachable (using `cache_get_key`).

Example 1:

```python
from wise.utils.rate_limit import rate_limit_func
@rate_limit_func(24 * 60 * 60) # once a day
def foo():
   ...

foo() # will be called only once a day
```

Example 2:

```python
from datetime import timedelta
from wise.utils.rate_limit import rate_limit_func

@rate_limit_func(timedelta(milliseconds=10)) # once every 10ms
def bar():
   ...
```

Example 3:

```python
from datetime import timedelta
from wise.utils.rate_limit import rate_limit_func

@rate_limit_func(None)
def foobar(x):
    ...


foobar(x=12345, rate_limit_period=12 * 60 * 60)
```

### Important notes:

#### Management Commands
Wise adds some management commands to your project, which you should run in your entrypoint/startup script:
```bash
manage.py consume
manage.py serve_metrics
manage.py wise_setup # (this should be run after 'manage.py migrate')
```

#### Running Celery

1. Run celery beat *only one* of your pods (like worker-master).

    Add this to your worker.ini or worker-master.ini (or other ini file):

    ```bash
    celery -A wise.utils beat --loglevel=INFO
    ```

2. Run celery worker in any any of pods you want.

   Add this to your worker.ini or worker-master.ini (or other ini file):

    ```bash
    celery -A wise.utils worker --loglevel=INFO --concurrency=CONCURRENCY
    ```
    and replace `CONCURRENCY` with the number of workers you want.

3. Add celery periodic tasks (in your project's admin panel) (post-deploy):

   Here are the celery tasks that you should/can add periodic tasks for:

   1. `wise.tasks.publish_everything` (low frequency)
   2. `wise.tasks.publish_recently_updated_objects` (high frequency)
   3. `wise.tasks.update_everything` (up to you)
   4. `wise.tasks.update_set` (you should provide an argument for this one)
   5. `wise.tasks.rebuild_publisher_heaps` (low frequency)
   6. `wise.tasks.update_publisher_heaps` (high frequency)
   7. `wise.tasks.sync_updater_heaps` (high frequency)


## Development

### Installing Dependencies

Use venv:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:

```bash
make install
```

### Pre-commit

Run pre-commit hooks:

```bash
make pre-commit
```

### Publish

#### Setup your PyPI credentials:

Find the PyPI credentials in safe.wisdomise.com (look for "PyPI credentials"). Copy it to your local `~/.pypirc` file.


#### Publish to PyPI

```bash
make publish
```

This command also runs pre-commit hooks.
