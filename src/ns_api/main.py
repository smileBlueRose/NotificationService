from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from loguru import logger

from common.config import settings
from common.db import Database
from ns_api.event_publisher import EventPublisher
from ns_api.repository import AcceptedEventRepository
from ns_api.router import router
from ns_api.use_case import AcceptEventUseCase


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    database = Database()
    event_publisher = EventPublisher()

    await database.connect()
    await event_publisher.start()
    logger.info("ns_api started")

    accepted_event_repository = AcceptedEventRepository(database.pool)
    app.state.accept_event_use_case = AcceptEventUseCase(
        accepted_event_repository=accepted_event_repository,
        event_publisher=event_publisher,
    )

    yield

    await event_publisher.stop()
    await database.disconnect()
    logger.info("ns_api stopped")


app = FastAPI(title="NS API", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host=settings.api.host, port=settings.api.port)