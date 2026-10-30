from datetime import UTC

import grpc
from google.protobuf import json_format
from pydantic import ValidationError

from common.errors import ServiceUnavailableError
from common.models import Event
from event_contract import events_pb2, events_pb2_grpc
from ns_api.use_case import AcceptEventUseCase

EVENT_TYPE_PREFIX = "EVENT_TYPE_"


class EventService(events_pb2_grpc.EventServiceServicer):
    def __init__(self, accept_event_use_case: AcceptEventUseCase) -> None:
        self._accept_event_use_case = accept_event_use_case

    async def AcceptEvent(
        self,
        request: events_pb2.Event,
        context: grpc.aio.ServicerContext,
    ) -> events_pb2.AcceptEventResponse:
        try:
            event = self._to_event(request)
        except ValidationError as error:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(error))
        try:
            await self._accept_event_use_case.execute(event)
        except ServiceUnavailableError as error:
            await context.abort(grpc.StatusCode.UNAVAILABLE, str(error))
        return events_pb2.AcceptEventResponse(status="accepted")

    @staticmethod
    def _to_event(request: events_pb2.Event) -> Event:
        event_type_name = events_pb2.EventType.Name(request.event_type)
        return Event(
            event_id=request.event_id,
            event_type=event_type_name.removeprefix(EVENT_TYPE_PREFIX).lower(),
            recipient_id=request.recipient_id,
            created_at=request.created_at.ToDatetime(tzinfo=UTC),
            payload=json_format.MessageToDict(request.payload),
        )
