import asyncio
import random

from aiokafka import ConsumerRecord
from loguru import logger
from pydantic import ValidationError

from common.config import settings
from common.errors import TRANSIENT_ERRORS
from common.models import Event
from ns_processor.dead_letter_publisher import DeadLetterPublisher
from ns_processor.use_case import ProcessEventUseCase


class EventMessageHandler:
    def __init__(self, use_case: ProcessEventUseCase, dead_letter_publisher: DeadLetterPublisher) -> None:
        self._use_case = use_case
        self._dead_letter_publisher = dead_letter_publisher

    async def handle(self, message: ConsumerRecord) -> None:
        try:
            event = Event.model_validate_json(message.value)
        except ValidationError as error:
            logger.error("invalid_event offset={} error={!r}", message.offset, error)
            await self._send_to_dead_letter(message, error)
            return

        for attempt in range(1, settings.processor.max_attempts + 1):
            try:
                await self._use_case.execute(event)
                return
            except Exception as error:
                if attempt == settings.processor.max_attempts:
                    logger.error("event_processing_failed event_id={} error={!r}", event.event_id, error)
                    await self._send_to_dead_letter(message, error)
                    return
                delay_seconds = self._calculate_delay(attempt)
                logger.warning(
                    "event_processing_retry event_id={} attempt={} retry_in={:.2f}s error={!r}",
                    event.event_id,
                    attempt,
                    delay_seconds,
                    error,
                )
                await asyncio.sleep(delay_seconds)

    async def _send_to_dead_letter(self, message: ConsumerRecord, error: Exception) -> None:
        while True:
            try:
                await self._dead_letter_publisher.publish(message, error)
                return
            except TRANSIENT_ERRORS as publish_error:
                logger.warning("dead_letter_publish_failed offset={} error={!r}", message.offset, publish_error)
                await asyncio.sleep(settings.processor.base_retry_delay_seconds)

    @staticmethod
    def _calculate_delay(attempt: int) -> float:
        exponential_delay = settings.processor.base_retry_delay_seconds * 2 ** (attempt - 1)
        half_delay = exponential_delay / 2
        return half_delay + random.uniform(0, half_delay)