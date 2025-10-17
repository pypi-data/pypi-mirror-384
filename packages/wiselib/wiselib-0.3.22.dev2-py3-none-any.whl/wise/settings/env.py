from pydantic import StrictStr, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    debug: bool
    secret_key: StrictStr
    service_name: StrictStr
    environment: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="",
        env_nested_delimiter="__",
        env_file=".env",
        extra="allow",  # Ignore extra fields
    )


class SentrySettings(BaseModel):
    enabled: bool = False
    dsn: str = ""
    environment: str = "production"
    sample_rate: float | int = 1.0


class KafkaSettings(BaseModel):
    enabled: bool = True
    bootstrap_servers: StrictStr
    security_protocol: StrictStr
    sasl_mechanism: StrictStr
    username: StrictStr
    password: StrictStr
    group_id: StrictStr
    max_poll_records: int = 500
    max_poll_interval_ms: int = 300000


class PostgresSettings(BaseModel):
    name: StrictStr
    user: StrictStr
    password: StrictStr
    host: StrictStr
    port: int


class RedisSettings(BaseModel):
    host: StrictStr
    port: int
    db: int = 0
    user: StrictStr | None = None
    password: StrictStr | None = None


class CelerySettings(BaseModel):
    enabled: bool = True
    broker_url: StrictStr
    default_queue: StrictStr = ""


class PrometheusSettings(BaseModel):
    enabled: bool = True
    prefix: StrictStr
    multiproc_dir: StrictStr = "/tmp/multiproc-tmp"


class TracingSettings(BaseModel):
    url: StrictStr = ""
    enabled: bool = False
    service_name: StrictStr = ""
    sample_ratio: float | int = 0.1
