class EventDeliveryError(Exception):
    pass


class EventRejectedError(EventDeliveryError):
    pass


class RetriesExhaustedError(EventDeliveryError):
    pass