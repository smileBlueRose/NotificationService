import asyncpg

from common.models import Notification, NotificationStatus, Platform
from ns_processor.models import Recipient


class RecipientRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, recipient_id: int) -> Recipient | None:
        recipient_row = await self._pool.fetchrow(
            "SELECT recipient_id, email, email_enabled, push_enabled, locale FROM recipients WHERE recipient_id = $1",
            recipient_id,
        )
        if recipient_row is None:
            return None
        device_rows = await self._pool.fetch(
            "SELECT device_token, platform FROM recipient_devices WHERE recipient_id = $1",
            recipient_id,
        )
        devices = [
            RecipientDevice(device_token=row["device_token"], platform=Platform(row["platform"])) for row in device_rows
        ]
        return Recipient(
            recipient_id=recipient_row["recipient_id"],
            email=recipient_row["email"],
            email_enabled=recipient_row["email_enabled"],
            push_enabled=recipient_row["push_enabled"],
            locale=recipient_row["locale"],
            devices=devices,
        )


class NotificationRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def add_pending(self, notifications: list[Notification]) -> None:
        await self._pool.executemany(
            "INSERT INTO notifications (notification_id, event_id, channel, target, status) "
            "VALUES ($1, $2, $3, $4, $5) ON CONFLICT (notification_id) DO NOTHING",
            [
                (
                    notification.notification_id,
                    notification.event_id,
                    notification.channel.value,
                    notification.target,
                    NotificationStatus.PENDING.value,
                )
                for notification in notifications
            ],
        )
