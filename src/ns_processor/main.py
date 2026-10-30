import asyncio

from aiokafka import AIOKafkaConsumer
from loguru import logger

from common.config import settings
from common.db import Database
from ns_processor.dead_letter_publisher import DeadLetterPublisher
from ns_processor.message_handler import EventMessageHandler
from ns_processor.notification_publisher import NotificationPublisher
from ns_processor.repository import NotificationRepository, RecipientRepository
from ns_processor.use_case import ProcessEventUseCase


async def run() -> None:
    database = Database()
    notification_publisher = NotificationPublisher()
    dead_letter_publisher = DeadLetterPublisher()
    consumer = AIOKafkaConsumer(
        settings.kafka.events_topic,
        bootstrap_servers=settings.kafka.bootstrap_servers,
        group_id=settings.processor.group_id,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )

    await database.connect()
    await notification_publisher.start()
    await dead_letter_publisher.start()
    await consumer.start()
    logger.info("ns_processor started")

    use_case = ProcessEventUseCase(
        recipient_repository=RecipientRepository(database.pool),
        notification_repository=NotificationRepository(database.pool),
        notification_publisher=notification_publisher,
    )
    message_handler = EventMessageHandler(use_case=use_case, dead_letter_publisher=dead_letter_publisher)

    try:
        async for message in consumer:
            await message_handler.handle(message)
            await consumer.commit()
    finally:
        await consumer.stop()
        await dead_letter_publisher.stop()
        await notification_publisher.stop()
        await database.disconnect()
        logger.info("ns_processor stopped")


if __name__ == "__main__":
    asyncio.run(run())
