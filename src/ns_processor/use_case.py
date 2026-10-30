from uuid import UUID, uuid5

from loguru import logger

from common.models import Channel, Event, Notification
from ns_processor.models import Recipient
from ns_processor.notification_publisher import NotificationPublisher
from ns_processor.repository import NotificationRepository, RecipientRepository


class ProcessEventUseCase:
    def __init__(
        self,
        recipient_repository: RecipientRepository,
        notification_repository: NotificationRepository,
        notification_publisher: NotificationPublisher,
    ) -> None:
        self._recipient_repository = recipient_repository
        self._notification_repository = notification_repository
        self._notification_publisher = notification_publisher

    async def execute(self, event: Event) -> None:
        recipient = await self._recipient_repository.get(event.recipient_id)
        if recipient is None:
            logger.warning("unknown_recipient event_id={} recipient_id={}", event.event_id, event.recipient_id)
            return

        notifications = self._create_notifications(event, recipient)
        if not notifications:
            logger.info("no_enabled_channels event_id={} recipient_id={}", event.event_id, event.recipient_id)
            return

        await self._notification_repository.add_pending(notifications)
        await self._notification_publisher.publish(notifications)
        logger.info("event_processed event_id={} notifications={}", event.event_id, len(notifications))

    def _create_notifications(self, event: Event, recipient: Recipient) -> list[Notification]:
        notifications: list[Notification] = []
        if recipient.email_enabled and recipient.email is not None:
            notifications.append(self._create_notification(event, recipient, Channel.EMAIL, recipient.email))
        if recipient.push_enabled:
            for device in recipient.devices:
                notification = self._create_notification(event, recipient, Channel.PUSH, device.device_token)
                notifications.append(notification.model_copy(update={"platform": device.platform}))
        return notifications

    def _create_notification(
        self,
        event: Event,
        recipient: Recipient,
        channel: Channel,
        target: str,
    ) -> Notification:
        return Notification(
            notification_id=self._build_notification_id(event.event_id, channel, target),
            event_id=event.event_id,
            event_type=event.event_type,
            channel=channel,
            target=target,
            locale=recipient.locale,
            payload=event.payload,
        )

    @staticmethod
    def _build_notification_id(event_id: UUID, channel: Channel, target: str) -> UUID:
        return uuid5(event_id, f"{channel.value}:{target}")
