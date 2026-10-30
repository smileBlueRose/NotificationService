from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseModel):
    bootstrap_servers: str
    publish_timeout_seconds: float
    events_topic: str
    email_topic: str
    push_topic: str
    events_dlq_topic: str


class ApiSettings(BaseModel):
    host: str
    port: int


class DatabaseSettings(BaseModel):
    host: str
    port: int

    user: str
    name: str
    password: str

    pool_min_size: int = 2
    pool_max_size: int = 10
    command_timeout_seconds: int = 1


class ProcessorSettings(BaseModel):
    group_id: str
    base_retry_delay_seconds: float
    max_attempts: int


class MockProvidersSettings(BaseModel):
    host: str
    port: int
    failure_rate: float


class WorkerSettings(BaseModel):
    group_id_prefix: str
    providers_base_url: str
    provider_timeout_seconds: float
    infrastructure_retry_delay_seconds: float


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    kafka: KafkaSettings
    api: ApiSettings
    db: DatabaseSettings
    processor: ProcessorSettings
    mock_providers: MockProvidersSettings
    worker: WorkerSettings


settings = Settings()
