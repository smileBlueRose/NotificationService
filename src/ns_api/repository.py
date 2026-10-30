from uuid import UUID

import asyncpg


class AcceptedEventRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def exists(self, event_id: UUID) -> bool:
        return await self._pool.fetchval(
            "SELECT EXISTS (SELECT 1 FROM accepted_events WHERE event_id = $1)",
            event_id,
        )

    async def add(self, event_id: UUID) -> None:
        await self._pool.execute(
            "INSERT INTO accepted_events (event_id) VALUES ($1) ON CONFLICT (event_id) DO NOTHING",
            event_id,
        )
