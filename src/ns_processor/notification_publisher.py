import asyncio

from common.config import settings
from common.kafka_producer import KafkaProducer
from common.models import Channel, Notification


class NotificationPublisher:
    def __init__(self, kafka_producer: KafkaProducer) -> None:
        self._kafka_producer = kafka_producer
        self._topics_by_channel = {
            Channel.EMAIL: settings.kafka.email_topic,
            Channel.PUSH: settings.kafka.push_topic,
        }

    async def publish(self, notifications: list[Notification]) -> None:
        sends = [self._publish_one(notification) for notification in notifications]
        await asyncio.gather(*sends)

    async def _publish_one(self, notification: Notification) -> None:
        await self._kafka_producer.send(
            topic=self._topics_by_channel[notification.channel],
            key=str(notification.notification_id).encode(),
            value=notification.model_dump_json().encode(),
        )