from loguru import logger

from common.models import Notification, NotificationStatus
from ns_worker.notification_publisher import NotificationPublisher
from ns_worker.provider_client import ProviderClient, ProviderDeliveryError
from ns_worker.repository import NotificationRepository
from ns_worker.templates import render_text
from ns_worker.topics import ChannelTopics


class DeliverNotificationUseCase:
    def __init__(
        self,
        notification_repository: NotificationRepository,
        provider_client: ProviderClient,
        notification_publisher: NotificationPublisher,
        channel_topics: ChannelTopics,
    ) -> None:
        self._notification_repository = notification_repository
        self._provider_client = provider_client
        self._notification_publisher = notification_publisher
        self._channel_topics = channel_topics

    async def execute(self, notification: Notification) -> None:
        status = await self._notification_repository.get_status(notification.notification_id)
        if status is None:
            logger.warning("unknown_notification notification_id={}", notification.notification_id)
            return
        if status == NotificationStatus.SENT:
            logger.info("duplicate_notification notification_id={}", notification.notification_id)
            return

        attempts = notification.attempts + 1
        try:
            await self._provider_client.send(notification, render_text(notification))
        except ProviderDeliveryError as error:
            await self._handle_failure(notification, attempts, str(error))
            return

        await self._notification_repository.mark_sent(notification.notification_id, attempts)
        logger.info("notification_sent notification_id={} attempts={}", notification.notification_id, attempts)

    async def _handle_failure(self, notification: Notification, attempts: int, error: str) -> None:
        next_topic = self._channel_topics.next_topic_after(attempts)
        retry_notification = notification.model_copy(update={"attempts": attempts})
        if next_topic == self._channel_topics.dead_letter:
            await self._notification_repository.mark_failed(notification.notification_id, attempts, error)
            logger.error(
                "notification_failed notification_id={} attempts={} error={}",
                notification.notification_id,
                attempts,
                error,
            )
        else:
            await self._notification_repository.mark_retrying(notification.notification_id, attempts, error)
            logger.warning(
                "notification_retry notification_id={} attempts={} next_topic={} error={}",
                notification.notification_id,
                attempts,
                next_topic,
                error,
            )
        await self._notification_publisher.publish(retry_notification, next_topic)
