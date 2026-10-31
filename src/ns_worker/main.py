import argparse
import asyncio
import time

import httpx
from aiokafka import AIOKafkaConsumer
from loguru import logger
from pydantic import ValidationError

from common.config import settings
from common.db import Database
from common.errors import TRANSIENT_ERRORS
from common.kafka_producer import KafkaProducer
from common.models import Channel, Notification
from ns_worker.notification_publisher import NotificationPublisher
from ns_worker.provider_client import ProviderClient
from ns_worker.repository import NotificationRepository
from ns_worker.topics import ChannelTopics
from ns_worker.use_case import DeliverNotificationUseCase


def parse_channel() -> Channel:
    parser = argparse.ArgumentParser(description="Notification worker")
    parser.add_argument("--channel", required=True, choices=[channel.value for channel in Channel])
    arguments = parser.parse_args()
    return Channel(arguments.channel)


def create_consumer(topic: str) -> AIOKafkaConsumer:
    return AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.kafka.bootstrap_servers,
        group_id=f"{settings.worker.group_id_prefix}-{topic}",
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )


async def wait_until_ready(message_timestamp_ms: int, delay_seconds: int) -> None:
    ready_at = message_timestamp_ms / 1000 + delay_seconds
    wait_seconds = ready_at - time.time()
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)


async def deliver_until_processed(use_case: DeliverNotificationUseCase, notification: Notification) -> None:
    while True:
        try:
            await use_case.execute(notification)
            return
        except TRANSIENT_ERRORS as error:
            logger.warning(
                "notification_processing_failed notification_id={} error={!r}",
                notification.notification_id,
                error,
            )
            await asyncio.sleep(settings.worker.infrastructure_retry_delay_seconds)


async def consume_topic(topic: str, delay_seconds: int, use_case: DeliverNotificationUseCase) -> None:
    consumer = create_consumer(topic)
    await consumer.start()
    logger.info("consumer_started topic={} delay_seconds={}", topic, delay_seconds)
    try:
        async for message in consumer:
            try:
                notification = Notification.model_validate_json(message.value)
            except ValidationError as error:
                logger.error("invalid_notification topic={} offset={} error={!r}", topic, message.offset, error)
                await consumer.commit()
                continue
            await wait_until_ready(message.timestamp, delay_seconds)
            await deliver_until_processed(use_case, notification)
            await consumer.commit()
    finally:
        await consumer.stop()


async def run(channel: Channel) -> None:
    channel_topics = ChannelTopics.for_channel(channel)
    database = Database()
    kafka_producer = KafkaProducer()

    await database.connect()
    await kafka_producer.start()

    async with httpx.AsyncClient(
        base_url=settings.worker.providers_base_url,
        timeout=settings.worker.provider_timeout_seconds,
    ) as http_client:
        use_case = DeliverNotificationUseCase(
            notification_repository=NotificationRepository(database.pool),
            provider_client=ProviderClient(http_client),
            notification_publisher=NotificationPublisher(kafka_producer),
            channel_topics=channel_topics,
        )
        consumers = [consume_topic(channel_topics.main, 0, use_case)]
        consumers += [
            consume_topic(retry_topic.name, retry_topic.delay_seconds, use_case)
            for retry_topic in channel_topics.retries
        ]
        logger.info("ns_worker started channel={}", channel.value)
        try:
            await asyncio.gather(*consumers)
        finally:
            await kafka_producer.stop()
            await database.disconnect()
            logger.info("ns_worker stopped channel={}", channel.value)


if __name__ == "__main__":
    asyncio.run(run(parse_channel()))