import asyncpg
from aiokafka.errors import KafkaError


class ServiceUnavailableError(Exception):
    pass

TRANSIENT_ERRORS = (
    TimeoutError,
    OSError,
    asyncpg.PostgresConnectionError,
    asyncpg.ConnectionDoesNotExistError,
    KafkaError,
)