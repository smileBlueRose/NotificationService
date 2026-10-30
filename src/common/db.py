import asyncpg

from common.config import settings


class Database:
    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        # noinspection unresolved-references
        self._pool = await asyncpg.create_pool(
            host=settings.db.host,
            port=settings.db.port,
            user=settings.db.user,
            password=settings.db.password,
            database=settings.db.name,
            min_size=settings.db.pool_min_size,
            max_size=settings.db.pool_max_size,
            command_timeout=settings.db.command_timeout_seconds,
        )

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database is not connected")
        return self._pool
