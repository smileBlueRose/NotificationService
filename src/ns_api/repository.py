from uuid import UUID

import asyncpg

from common.errors import ServiceUnavailableError

DATABASE_UNAVAILABLE_ERRORS = (
    TimeoutError,
    OSError,
    asyncpg.PostgresConnectionError,
    asyncpg.ConnectionDoesNotExistError,
)


class AcceptedEventRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def exists(self, event_id: UUID) -> bool:
        try:
            return await self._pool.fetchval(
                "SELECT EXISTS (SELECT 1 FROM accepted_events WHERE event_id = $1)",
                event_id,
            )
        except DATABASE_UNAVAILABLE_ERRORS as error:
            raise ServiceUnavailableError("Database is unavailable") from error

    async def add(self, event_id: UUID) -> None:
        try:
            await self._pool.execute(
                "INSERT INTO accepted_events (event_id) VALUES ($1) ON CONFLICT (event_id) DO NOTHING",
                event_id,
            )
        except DATABASE_UNAVAILABLE_ERRORS as error:
            raise ServiceUnavailableError("Database is unavailable") from error
