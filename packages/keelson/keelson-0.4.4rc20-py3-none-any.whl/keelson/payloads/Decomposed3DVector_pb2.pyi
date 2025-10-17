from google.protobuf import timestamp_pb2 as _timestamp_pb2
from foxglove import Vector3_pb2 as _Vector3_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Decomposed3DVector(_message.Message):
    __slots__ = ("timestamp", "frame_id", "vector")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    frame_id: str
    vector: _Vector3_pb2.Vector3
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., frame_id: _Optional[str] = ..., vector: _Optional[_Union[_Vector3_pb2.Vector3, _Mapping]] = ...) -> None: ...
