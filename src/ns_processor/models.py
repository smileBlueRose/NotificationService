from dataclasses import dataclass
from common.models import Platform


@dataclass(frozen=True)
class RecipientDevice:
    device_token: str
    platform: Platform


@dataclass(frozen=True)
class Recipient:
    recipient_id: int
    email: str | None
    email_enabled: bool
    push_enabled: bool
    locale: str
    devices: list[RecipientDevice]
