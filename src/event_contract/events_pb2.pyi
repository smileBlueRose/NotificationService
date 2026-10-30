import datetime

from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EVENT_TYPE_UNSPECIFIED: _ClassVar[EventType]
    EVENT_TYPE_USER_REGISTERED: _ClassVar[EventType]
    EVENT_TYPE_PASSWORD_RESET: _ClassVar[EventType]
    EVENT_TYPE_PIN_LIKED: _ClassVar[EventType]
    EVENT_TYPE_PIN_COMMENTED: _ClassVar[EventType]
    EVENT_TYPE_USER_FOLLOWED: _ClassVar[EventType]
EVENT_TYPE_UNSPECIFIED: EventType
EVENT_TYPE_USER_REGISTERED: EventType
EVENT_TYPE_PASSWORD_RESET: EventType
EVENT_TYPE_PIN_LIKED: EventType
EVENT_TYPE_PIN_COMMENTED: EventType
EVENT_TYPE_USER_FOLLOWED: EventType

class Event(_message.Message):
    __slots__ = ("event_id", "event_type", "recipient_id", "created_at", "payload")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    event_type: EventType
    recipient_id: int
    created_at: _timestamp_pb2.Timestamp
    payload: _struct_pb2.Struct
    def __init__(self, event_id: _Optional[str] = ..., event_type: _Optional[_Union[EventType, str]] = ..., recipient_id: _Optional[int] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., payload: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class AcceptEventResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...
