from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EVENT_TYPE_UNSPECIFIED: _ClassVar[EventType]
    EVENT_TYPE_USER_PENDING: _ClassVar[EventType]
    EVENT_TYPE_SYSTEM_PENDING: _ClassVar[EventType]
    EVENT_TYPE_FINISHED: _ClassVar[EventType]
    EVENT_TYPE_ERROR: _ClassVar[EventType]
EVENT_TYPE_UNSPECIFIED: EventType
EVENT_TYPE_USER_PENDING: EventType
EVENT_TYPE_SYSTEM_PENDING: EventType
EVENT_TYPE_FINISHED: EventType
EVENT_TYPE_ERROR: EventType

class EventSeries(_message.Message):
    __slots__ = ("count", "last_observed_time")
    COUNT_FIELD_NUMBER: _ClassVar[int]
    LAST_OBSERVED_TIME_FIELD_NUMBER: _ClassVar[int]
    count: int
    last_observed_time: _timestamp_pb2.Timestamp
    def __init__(self, count: _Optional[int] = ..., last_observed_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Event(_message.Message):
    __slots__ = ("timestamp", "reason", "regarding", "event_type", "series")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    REGARDING_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    SERIES_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    reason: str
    regarding: str
    event_type: EventType
    series: EventSeries
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., reason: _Optional[str] = ..., regarding: _Optional[str] = ..., event_type: _Optional[_Union[EventType, str]] = ..., series: _Optional[_Union[EventSeries, _Mapping]] = ...) -> None: ...

class ListEventsRequest(_message.Message):
    __slots__ = ("regarding_glob", "matching_event_types", "timestamp_after", "cursor")
    REGARDING_GLOB_FIELD_NUMBER: _ClassVar[int]
    MATCHING_EVENT_TYPES_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_AFTER_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    regarding_glob: str
    matching_event_types: _containers.RepeatedScalarFieldContainer[EventType]
    timestamp_after: _timestamp_pb2.Timestamp
    cursor: str
    def __init__(self, regarding_glob: _Optional[str] = ..., matching_event_types: _Optional[_Iterable[_Union[EventType, str]]] = ..., timestamp_after: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., cursor: _Optional[str] = ...) -> None: ...

class ListEventsResponse(_message.Message):
    __slots__ = ("events", "cursor")
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[Event]
    cursor: str
    def __init__(self, events: _Optional[_Iterable[_Union[Event, _Mapping]]] = ..., cursor: _Optional[str] = ...) -> None: ...

class ListenForEventsRequest(_message.Message):
    __slots__ = ("regarding_glob", "matching_event_types", "timestamp_after")
    REGARDING_GLOB_FIELD_NUMBER: _ClassVar[int]
    MATCHING_EVENT_TYPES_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_AFTER_FIELD_NUMBER: _ClassVar[int]
    regarding_glob: str
    matching_event_types: _containers.RepeatedScalarFieldContainer[EventType]
    timestamp_after: _timestamp_pb2.Timestamp
    def __init__(self, regarding_glob: _Optional[str] = ..., matching_event_types: _Optional[_Iterable[_Union[EventType, str]]] = ..., timestamp_after: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ListenForEventsResponse(_message.Message):
    __slots__ = ("events",)
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[Event]
    def __init__(self, events: _Optional[_Iterable[_Union[Event, _Mapping]]] = ...) -> None: ...
