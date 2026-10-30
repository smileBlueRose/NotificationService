from loguru import logger

from common.models import Event
from ns_api.event_publisher import EventPublisher
from ns_api.repository import AcceptedEventRepository


class AcceptEventUseCase:
    def __init__(
        self,
        accepted_event_repository: AcceptedEventRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._accepted_event_repository = accepted_event_repository
        self._event_publisher = event_publisher

    async def execute(self, event: Event) -> None:
        if await self._accepted_event_repository.exists(event.event_id):
            logger.info("duplicate_event event_id={}", event.event_id)
            return
        await self._event_publisher.publish(event)
        await self._accepted_event_repository.add(event.event_id)