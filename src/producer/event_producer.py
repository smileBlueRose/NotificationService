import asyncio
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import httpx
from loguru import logger

from common.models import Event, EventType
from producer.errors import EventRejectedError, RetriesExhaustedError
from producer.retry_policy import RetryPolicy


class EventProducer:
    def __init__(self, http_client: httpx.AsyncClient, retry_policy: RetryPolicy) -> None:
        self._http_client = http_client
        self._retry_policy = retry_policy

    async def send_event(
        self,
        event_type: EventType,
        recipient_id: int,
        payload: dict[str, Any],
    ) -> UUID:
        event = Event(
            event_id=uuid4(),
            event_type=event_type,
            recipient_id=recipient_id,
            created_at=datetime.now(UTC),
            payload=payload,
        )
        started_at = time.monotonic()
        attempt = 1
        while True:
            if await self._try_send(event, attempt):
                return event.event_id
            delay_seconds = self._retry_policy.delay_before_next_attempt(attempt)
            elapsed_seconds = time.monotonic() - started_at
            if not self._retry_policy.can_retry(attempt, elapsed_seconds, delay_seconds):
                raise RetriesExhaustedError(f"Event {event.event_id} was not delivered after {attempt} attempts")
            await asyncio.sleep(delay_seconds)
            attempt += 1

    async def _try_send(self, event: Event, attempt: int) -> bool:
        try:
            response = await self._http_client.post(
                "/v1/events",
                content=event.model_dump_json(),
                headers={"Content-Type": "application/json"},
            )
        except httpx.TransportError as error:
            logger.warning("event_send_failed event_id={} attempt={} error={!r}", event.event_id, attempt, error)
            return False
        if response.status_code == httpx.codes.ACCEPTED:
            return True
        if self._retry_policy.is_retryable_status(response.status_code):
            logger.warning(
                "event_send_failed event_id={} attempt={} status={}",
                event.event_id,
                attempt,
                response.status_code,
            )
            return False
        raise EventRejectedError(f"Event {event.event_id} rejected with status {response.status_code}")