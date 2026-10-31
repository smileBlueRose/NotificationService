import asyncio
import multiprocessing

import grpc
from loguru import logger

from common.config import settings
from common.db import Database
from common.kafka_producer import KafkaProducer
from event_contract import events_pb2_grpc
from ns_api.event_publisher import EventPublisher
from ns_api.grpc.service import EventService
from ns_api.repository import AcceptedEventRepository
from ns_api.use_case import AcceptEventUseCase


async def run() -> None:
    database = Database()
    kafka_producer = KafkaProducer(linger_ms=settings.kafka.linger_ms)

    await database.connect()
    await kafka_producer.start()

    accept_event_use_case = AcceptEventUseCase(
        accepted_event_repository=AcceptedEventRepository(database.pool),
        event_publisher=EventPublisher(kafka_producer),
    )

    server = grpc.aio.server(options=[("grpc.so_reuseport", 1)])
    events_pb2_grpc.add_EventServiceServicer_to_server(EventService(accept_event_use_case), server)
    address = f"{settings.api.host}:{settings.api.grpc_port}"
    server.add_insecure_port(address)

    await server.start()
    logger.info("ns_api_grpc started address={}", address)
    try:
        await server.wait_for_termination()
    finally:
        await server.stop(grace=5)
        await kafka_producer.stop()
        await database.disconnect()
        logger.info("ns_api_grpc stopped")


def serve() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    spawn_context = multiprocessing.get_context("spawn")
    processes = [spawn_context.Process(target=serve) for _ in range(settings.api.workers)]
    for process in processes:
        process.start()
    for process in processes:
        process.join()