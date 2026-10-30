from aiokafka import AIOKafkaProducer

from common.config import settings
from common.models import Event


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
        await self._producer.send_and_wait(
            topic=settings.kafka.events_topic,
            key=str(event.recipient_id).encode(),
            value=event.model_dump_json().encode(),
        )