import asyncio

from aiokafka import AIOKafkaProducer

from common.config import settings
from common.models import Channel, Notification


class NotificationPublisher:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None
        self._topics_by_channel = {
            Channel.EMAIL: settings.kafka.email_topic,
            Channel.PUSH: settings.kafka.push_topic,
        }

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka.bootstrap_servers,
            acks="all",
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()

    async def publish(self, notifications: list[Notification]) -> None:
        if self._producer is None:
            raise RuntimeError("NotificationPublisher is not started")
        async with asyncio.timeout(settings.kafka.publish_timeout_seconds):
            send_results = [
                await self._producer.send(
                    topic=self._topics_by_channel[notification.channel],
                    key=str(notification.notification_id).encode(),
                    value=notification.model_dump_json().encode(),
                )
                for notification in notifications
            ]
            await asyncio.gather(*send_results)
