from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from loguru import logger

from ns_api.event_publisher import EventPublisher
from common.config import settings
from common.models import Event

event_publisher = EventPublisher()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await event_publisher.start()
    logger.info("Kafka producer started")
    yield
    await event_publisher.stop()
    logger.info("Kafka producer stopped")


app = FastAPI(title="NS API", lifespan=lifespan)


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url='/docs')

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/events", status_code=status.HTTP_202_ACCEPTED)
async def accept_event(event: Event) -> dict[str, str]:
    await event_publisher.publish(event)
    return {"status": "accepted"}


if __name__ == "__main__":
    uvicorn.run(app, host=settings.api.host, port=settings.api.port)