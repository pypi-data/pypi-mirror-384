from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NetworkStatus(_message.Message):
    __slots__ = ("ping_sent_at", "pong_sent_at", "ping_host", "pong_host", "payload_size_mb", "round_trip_time_ms", "latency_ms", "clock_skew_ms")
    PING_SENT_AT_FIELD_NUMBER: _ClassVar[int]
    PONG_SENT_AT_FIELD_NUMBER: _ClassVar[int]
    PING_HOST_FIELD_NUMBER: _ClassVar[int]
    PONG_HOST_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_SIZE_MB_FIELD_NUMBER: _ClassVar[int]
    ROUND_TRIP_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    CLOCK_SKEW_MS_FIELD_NUMBER: _ClassVar[int]
    ping_sent_at: _timestamp_pb2.Timestamp
    pong_sent_at: _timestamp_pb2.Timestamp
    ping_host: str
    pong_host: str
    payload_size_mb: float
    round_trip_time_ms: float
    latency_ms: float
    clock_skew_ms: float
    def __init__(self, ping_sent_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., pong_sent_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., ping_host: _Optional[str] = ..., pong_host: _Optional[str] = ..., payload_size_mb: _Optional[float] = ..., round_trip_time_ms: _Optional[float] = ..., latency_ms: _Optional[float] = ..., clock_skew_ms: _Optional[float] = ...) -> None: ...
