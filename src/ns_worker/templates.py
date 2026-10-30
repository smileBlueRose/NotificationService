from string import Template

from common.models import EventType, Notification

TEMPLATES = {
    EventType.USER_REGISTERED: Template("Welcome! Your account has been created."),
    EventType.PASSWORD_RESET: Template("Use this code to reset your password: $code"),
    EventType.PIN_LIKED: Template("$actor liked your pin $pin_id"),
    EventType.PIN_COMMENTED: Template("$actor commented on your pin $pin_id: $comment"),
    EventType.USER_FOLLOWED: Template("$actor started following you"),
}


def render_text(notification: Notification) -> str:
    template = TEMPLATES[notification.event_type]
    return template.safe_substitute(notification.payload)