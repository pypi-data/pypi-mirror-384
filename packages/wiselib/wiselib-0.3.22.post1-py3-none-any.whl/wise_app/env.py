from functools import lru_cache

from dotenv import find_dotenv, load_dotenv
from pydantic import StrictStr
from pydantic_settings import SettingsConfigDict

from wise.settings.dependencies import DelphiSettings
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
    delphi: DelphiSettings

    model_config = SettingsConfigDict(
        env_prefix="WISE_",
        env_nested_delimiter="__",
        env_file=find_dotenv(raise_error_if_not_found=False),
        extra="allow",  # Ignore extra fields
    )


@lru_cache
def get_env_settings() -> EnvSettings:
    return EnvSettings()  # type: ignore
