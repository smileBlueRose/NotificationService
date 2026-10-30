from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from common.config import settings
from common.errors import ServiceUnavailableError
from common.models import Event
import asyncio


class EventPublisher:
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

    async def publish(self, event: Event) -> None:
        if self._producer is None:
            raise RuntimeError("EventPublisher is not started")
        try:
            async with asyncio.timeout(settings.kafka.publish_timeout_seconds):
                await self._producer.send_and_wait(
                    topic=settings.kafka.events_topic,
                    key=str(event.recipient_id).encode(),
                    value=event.model_dump_json().encode(),
                )
        except (TimeoutError, KafkaError) as error:
            raise ServiceUnavailableError("Kafka is unavailable") from error
