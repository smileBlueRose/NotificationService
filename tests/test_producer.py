import json

import httpx
import pytest

from common.models import EventType
from producer.errors import EventRejectedError, RetriesExhaustedError
from producer.event_producer import EventProducer
from producer.retry_policy import RetryPolicy

NO_DELAY_POLICY = RetryPolicy(
    max_attempts=3,
    base_delay_seconds=0.0,
    max_delay_seconds=0.0,
    deadline_seconds=10.0,
)


class FakeNotificationService:
    def __init__(self, outcomes: list[int | Exception]) -> None:
        self._outcomes = outcomes
        self.received_event_ids: list[str] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.received_event_ids.append(json.loads(request.content)["event_id"])
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return httpx.Response(outcome)


def build_producer(service: FakeNotificationService) -> EventProducer:
    transport = httpx.MockTransport(service.handle)
    http_client = httpx.AsyncClient(base_url="http://ns-api", transport=transport)
    return EventProducer(http_client=http_client, retry_policy=NO_DELAY_POLICY)


async def send_test_event(producer: EventProducer) -> str:
    event_id = await producer.send_event(
        event_type=EventType.PIN_LIKED,
        recipient_id=1,
        payload={"actor": "anna"},
    )
    return str(event_id)


async def test_returns_event_id_on_first_success() -> None:
    service = FakeNotificationService(outcomes=[202])
    producer = build_producer(service)

    event_id = await send_test_event(producer)

    assert service.received_event_ids == [event_id]


async def test_retries_on_server_error_with_same_event_id() -> None:
    service = FakeNotificationService(outcomes=[503, 500, 202])
    producer = build_producer(service)

    event_id = await send_test_event(producer)

    assert service.received_event_ids == [event_id, event_id, event_id]


async def test_retries_on_timeout() -> None:
    timeout_error = httpx.ReadTimeout("timeout")
    service = FakeNotificationService(outcomes=[timeout_error, 202])
    producer = build_producer(service)

    event_id = await send_test_event(producer)

    assert service.received_event_ids == [event_id, event_id]


async def test_does_not_retry_rejected_event() -> None:
    service = FakeNotificationService(outcomes=[422])
    producer = build_producer(service)

    with pytest.raises(EventRejectedError):
        await send_test_event(producer)

    assert len(service.received_event_ids) == 1


async def test_stops_after_max_attempts() -> None:
    service = FakeNotificationService(outcomes=[503, 503, 503])
    producer = build_producer(service)

    with pytest.raises(RetriesExhaustedError):
        await send_test_event(producer)

    assert len(service.received_event_ids) == NO_DELAY_POLICY.max_attempts
