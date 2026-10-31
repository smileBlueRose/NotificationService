from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from loguru import logger

from common.config import settings
from common.db import Database
from common.errors import ServiceUnavailableError
from common.kafka_producer import KafkaProducer
from ns_api.event_publisher import EventPublisher
from ns_api.repository import AcceptedEventRepository
from ns_api.rest.router import router
from ns_api.use_case import AcceptEventUseCase


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    database = Database()
    kafka_producer = KafkaProducer(linger_ms=settings.kafka.linger_ms)

    await database.connect()
    await kafka_producer.start()
    logger.info("ns_api started")

    app.state.accept_event_use_case = AcceptEventUseCase(
        accepted_event_repository=AcceptedEventRepository(database.pool),
        event_publisher=EventPublisher(kafka_producer),
    )

    yield

    await kafka_producer.stop()
    await database.disconnect()
    logger.info("ns_api stopped")


app = FastAPI(title="NS API", lifespan=lifespan)
app.include_router(router)


@app.exception_handler(ServiceUnavailableError)
async def handle_service_unavailable(request: Request, error: ServiceUnavailableError) -> JSONResponse:
    logger.warning("service_unavailable path={} reason={!r}", request.url.path, error.__cause__)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(error)},
    )


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "ns_api.rest.main:app",
        host=settings.api.host,
        port=settings.api.port,
        workers=settings.api.workers,
    )