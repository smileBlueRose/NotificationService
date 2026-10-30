from uuid import UUID

import asyncpg

from common.models import NotificationStatus


class NotificationRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_status(self, notification_id: UUID) -> NotificationStatus | None:
        status = await self._pool.fetchval(
            "SELECT status FROM notifications WHERE notification_id = $1",
            notification_id,
        )
        return NotificationStatus(status) if status is not None else None

    async def mark_sent(self, notification_id: UUID, attempts: int) -> None:
        await self._pool.execute(
            "UPDATE notifications SET status = $2, attempts = $3, last_error = NULL, sent_at = now() "
            "WHERE notification_id = $1 AND status <> $2",
            notification_id,
            NotificationStatus.SENT.value,
            attempts,
        )

    async def mark_retrying(self, notification_id: UUID, attempts: int, error: str) -> None:
        await self._update_failure(notification_id, NotificationStatus.RETRYING, attempts, error)

    async def mark_failed(self, notification_id: UUID, attempts: int, error: str) -> None:
        await self._update_failure(notification_id, NotificationStatus.FAILED, attempts, error)

    async def _update_failure(
        self,
        notification_id: UUID,
        status: NotificationStatus,
        attempts: int,
        error: str,
    ) -> None:
        await self._pool.execute(
            "UPDATE notifications SET status = $2, attempts = $3, last_error = $4 "
            "WHERE notification_id = $1 AND status <> $5",
            notification_id,
            status.value,
            attempts,
            error,
            NotificationStatus.SENT.value,
        )