import asyncio

import grpc
from loguru import logger

from common.config import settings
from common.db import Database
from event_contract import events_pb2_grpc
from ns_api.event_publisher import EventPublisher
from ns_api.grpc.service import EventService
from ns_api.repository import AcceptedEventRepository
from ns_api.use_case import AcceptEventUseCase


async def run() -> None:
    database = Database()
    event_publisher = EventPublisher()

    await database.connect()
    await event_publisher.start()

    accept_event_use_case = AcceptEventUseCase(
        accepted_event_repository=AcceptedEventRepository(database.pool),
        event_publisher=event_publisher,
    )

    server = grpc.aio.server()
    events_pb2_grpc.add_EventServiceServicer_to_server(EventService(accept_event_use_case), server)
    address = f"{settings.api.host}:{settings.api.grpc_port}"
    server.add_insecure_port(address)

    await server.start()
    logger.info("ns_api_grpc started address={}", address)
    try:
        await server.wait_for_termination()
    finally:
        await server.stop(grace=5)
        await event_publisher.stop()
        await database.disconnect()
        logger.info("ns_api_grpc stopped")


if __name__ == "__main__":
    asyncio.run(run())
