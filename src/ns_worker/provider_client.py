import httpx

from common.models import Channel, Notification, Platform


class ProviderDeliveryError(Exception):
    pass


class ProviderClient:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http_client = http_client

    async def send(self, notification: Notification, text: str) -> None:
        path = self._resolve_path(notification)
        try:
            response = await self._http_client.post(path, json={"target": notification.target, "text": text})
        except httpx.TransportError as error:
            raise ProviderDeliveryError(f"{path} request failed: {error!r}") from error
        if not response.is_success:
            raise ProviderDeliveryError(f"{path} responded with status {response.status_code}")

    @staticmethod
    def _resolve_path(notification: Notification) -> str:
        if notification.channel == Channel.EMAIL:
            return "/ses"
        if notification.platform == Platform.IOS:
            return "/apns"
        return "/fcm"