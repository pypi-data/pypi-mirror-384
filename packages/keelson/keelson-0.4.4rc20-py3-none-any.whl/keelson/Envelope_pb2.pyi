from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Envelope(_message.Message):
    __slots__ = ("enclosed_at", "payload")
    ENCLOSED_AT_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    enclosed_at: _timestamp_pb2.Timestamp
    payload: bytes
    def __init__(self, enclosed_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., payload: _Optional[bytes] = ...) -> None: ...

class KeyEnvelopePair(_message.Message):
    __slots__ = ("timestamp", "key", "envelope")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    ENVELOPE_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    key: str
    envelope: bytes
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., key: _Optional[str] = ..., envelope: _Optional[bytes] = ...) -> None: ...
