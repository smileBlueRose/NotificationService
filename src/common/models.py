from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(StrEnum):
    USER_REGISTERED = "user_registered"
    PASSWORD_RESET = "password_reset"
    PIN_LIKED = "pin_liked"
    PIN_COMMENTED = "pin_commented"
    USER_FOLLOWED = "user_followed"


class Channel(StrEnum):
    EMAIL = "email"
    PUSH = "push"


class Platform(StrEnum):
    IOS = "ios"
    ANDROID = "android"


class NotificationStatus(StrEnum):
    PENDING = "PENDING"
    RETRYING = "RETRYING"
    SENT = "SENT"
    FAILED = "FAILED"


class Event(BaseModel):
    event_id: UUID
    event_type: EventType
    recipient_id: int = Field(gt=0)
    created_at: datetime
    payload: dict[str, Any]


class Notification(BaseModel):
    notification_id: UUID
    event_id: UUID
    event_type: EventType
    channel: Channel
    target: str
    platform: Platform | None = None
    locale: str
    payload: dict[str, Any]
    attempts: int = 0