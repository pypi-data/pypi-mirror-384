from foxglove import PackedElementField_pb2 as _PackedElementField_pb2
from foxglove import Pose_pb2 as _Pose_pb2
from foxglove import Vector2_pb2 as _Vector2_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Grid(_message.Message):
    __slots__ = ("timestamp", "frame_id", "pose", "column_count", "cell_size", "row_stride", "cell_stride", "fields", "data")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    POSE_FIELD_NUMBER: _ClassVar[int]
    COLUMN_COUNT_FIELD_NUMBER: _ClassVar[int]
    CELL_SIZE_FIELD_NUMBER: _ClassVar[int]
    ROW_STRIDE_FIELD_NUMBER: _ClassVar[int]
    CELL_STRIDE_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    frame_id: str
    pose: _Pose_pb2.Pose
    column_count: int
    cell_size: _Vector2_pb2.Vector2
    row_stride: int
    cell_stride: int
    fields: _containers.RepeatedCompositeFieldContainer[_PackedElementField_pb2.PackedElementField]
    data: bytes
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., frame_id: _Optional[str] = ..., pose: _Optional[_Union[_Pose_pb2.Pose, _Mapping]] = ..., column_count: _Optional[int] = ..., cell_size: _Optional[_Union[_Vector2_pb2.Vector2, _Mapping]] = ..., row_stride: _Optional[int] = ..., cell_stride: _Optional[int] = ..., fields: _Optional[_Iterable[_Union[_PackedElementField_pb2.PackedElementField, _Mapping]]] = ..., data: _Optional[bytes] = ...) -> None: ...
