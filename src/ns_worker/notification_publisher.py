from common.kafka_producer import KafkaProducer
from common.models import Notification


class NotificationPublisher:
    def __init__(self, kafka_producer: KafkaProducer) -> None:
        self._kafka_producer = kafka_producer

    async def publish(self, notification: Notification, topic: str) -> None:
        await self._kafka_producer.send(
            topic=topic,
            key=str(notification.notification_id).encode(),
            value=notification.model_dump_json().encode(),
        )