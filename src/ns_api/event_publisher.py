from aiokafka.errors import KafkaError

from common.config import settings
from common.errors import ServiceUnavailableError
from common.kafka_producer import KafkaProducer
from common.models import Event


class EventPublisher:
    def __init__(self, kafka_producer: KafkaProducer) -> None:
        self._kafka_producer = kafka_producer

    async def publish(self, event: Event) -> None:
        try:
            await self._kafka_producer.send(
                topic=settings.kafka.events_topic,
                key=str(event.recipient_id).encode(),
                value=event.model_dump_json().encode(),
            )
        except (TimeoutError, KafkaError) as error:
            raise ServiceUnavailableError("Kafka is unavailable") from error