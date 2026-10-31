from aiokafka import ConsumerRecord

from common.config import settings
from common.kafka_producer import KafkaProducer


class DeadLetterPublisher:
    def __init__(self, kafka_producer: KafkaProducer) -> None:
        self._kafka_producer = kafka_producer

    async def publish(self, message: ConsumerRecord, error: Exception) -> None:
        headers = [
            ("error", repr(error).encode()),
            ("source_topic", message.topic.encode()),
            ("source_partition", str(message.partition).encode()),
            ("source_offset", str(message.offset).encode()),
        ]
        await self._kafka_producer.send(
            topic=settings.kafka.events_dlq_topic,
            key=message.key,
            value=message.value,
            headers=headers,
        )