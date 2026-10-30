from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseModel):
    bootstrap_servers: str
    events_topic: str
    publish_timeout_seconds: float | int


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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    kafka: KafkaSettings
    api: ApiSettings
    db: DatabaseSettings


settings = Settings()
