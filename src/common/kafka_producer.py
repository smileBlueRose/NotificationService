import asyncio

from aiokafka import AIOKafkaProducer

from common.config import settings


class KafkaProducer:
    def __init__(self, linger_ms: int = 0) -> None:
        self._linger_ms = linger_ms
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka.bootstrap_servers,
            acks="all",
            linger_ms=self._linger_ms,
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()

    async def send(
        self,
        topic: str,
        key: bytes | None,
        value: bytes,
        headers: list[tuple[str, bytes]] | None = None,
    ) -> None:
        if self._producer is None:
            raise RuntimeError("KafkaProducer is not started")
        async with asyncio.timeout(settings.kafka.publish_timeout_seconds):
            await self._producer.send_and_wait(topic=topic, key=key, value=value, headers=headers)