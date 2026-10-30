import random
from typing import Any

import uvicorn
from fastapi import FastAPI, Response, status
from loguru import logger

from common.config import settings

app = FastAPI(title="Mock Providers")


def simulate_delivery(provider: str, body: dict[str, Any]) -> Response:
    if random.random() < settings.mock_providers.failure_rate:
        logger.info("delivery_failed provider={} target={}", provider, body.get("target"))
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    logger.info("delivery_accepted provider={} target={}", provider, body.get("target"))
    return Response(status_code=status.HTTP_200_OK)


@app.post("/ses")
async def send_email(body: dict[str, Any]) -> Response:
    return simulate_delivery("ses", body)


@app.post("/fcm")
async def send_android_push(body: dict[str, Any]) -> Response:
    return simulate_delivery("fcm", body)


@app.post("/apns")
async def send_ios_push(body: dict[str, Any]) -> Response:
    return simulate_delivery("apns", body)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.mock_providers.host, port=settings.mock_providers.port)
