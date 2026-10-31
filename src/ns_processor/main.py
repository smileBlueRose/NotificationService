import asyncio

from aiokafka import AIOKafkaConsumer
from loguru import logger

from common.config import settings
from common.db import Database
from common.kafka_producer import KafkaProducer
from ns_processor.dead_letter_publisher import DeadLetterPublisher
from ns_processor.message_handler import EventMessageHandler
from ns_processor.notification_publisher import NotificationPublisher
from ns_processor.repository import NotificationRepository, RecipientRepository
from ns_processor.use_case import ProcessEventUseCase


async def run() -> None:
    database = Database()
    kafka_producer = KafkaProducer()
    consumer = AIOKafkaConsumer(
        settings.kafka.events_topic,
        bootstrap_servers=settings.kafka.bootstrap_servers,
        group_id=settings.processor.group_id,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )

    await database.connect()
    await kafka_producer.start()
    await consumer.start()
    logger.info("ns_processor started")

    use_case = ProcessEventUseCase(
        recipient_repository=RecipientRepository(database.pool),
        notification_repository=NotificationRepository(database.pool),
        notification_publisher=NotificationPublisher(kafka_producer),
    )
    message_handler = EventMessageHandler(
        use_case=use_case,
        dead_letter_publisher=DeadLetterPublisher(kafka_producer),
    )

    try:
        async for message in consumer:
            await message_handler.handle(message)
            await consumer.commit()
    finally:
        await consumer.stop()
        await kafka_producer.stop()
        await database.disconnect()
        logger.info("ns_processor stopped")


if __name__ == "__main__":
    asyncio.run(run())