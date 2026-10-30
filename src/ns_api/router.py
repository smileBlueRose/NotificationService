from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from common.models import Event
from ns_api.use_case import AcceptEventUseCase

router = APIRouter(prefix="/v1")


def get_accept_event_use_case(request: Request) -> AcceptEventUseCase:
    return request.app.state.accept_event_use_case


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def accept_event(
    event: Event,
    accept_event_use_case: Annotated[
        AcceptEventUseCase, Depends(get_accept_event_use_case)
    ],
) -> dict[str, str]:
    await accept_event_use_case.execute(event)
    return {"status": "accepted"}
