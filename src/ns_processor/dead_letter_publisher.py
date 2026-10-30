import asyncio

from aiokafka import AIOKafkaProducer, ConsumerRecord

from common.config import settings


class DeadLetterPublisher:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka.bootstrap_servers,
            acks="all",
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()

    async def publish(self, message: ConsumerRecord, error: Exception) -> None:
        if self._producer is None:
            raise RuntimeError("DeadLetterPublisher is not started")
        headers = [
            ("error", repr(error).encode()),
            ("source_topic", message.topic.encode()),
            ("source_partition", str(message.partition).encode()),
            ("source_offset", str(message.offset).encode()),
        ]
        async with asyncio.timeout(settings.kafka.publish_timeout_seconds):
            await self._producer.send_and_wait(
                topic=settings.kafka.events_dlq_topic,
                key=message.key,
                value=message.value,
                headers=headers,
            )