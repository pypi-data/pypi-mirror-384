from foxglove import PackedElementField_pb2 as _PackedElementField_pb2
from foxglove import Pose_pb2 as _Pose_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PointCloud(_message.Message):
    __slots__ = ("timestamp", "frame_id", "pose", "point_stride", "fields", "data")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    POSE_FIELD_NUMBER: _ClassVar[int]
    POINT_STRIDE_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    frame_id: str
    pose: _Pose_pb2.Pose
    point_stride: int
    fields: _containers.RepeatedCompositeFieldContainer[_PackedElementField_pb2.PackedElementField]
    data: bytes
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., frame_id: _Optional[str] = ..., pose: _Optional[_Union[_Pose_pb2.Pose, _Mapping]] = ..., point_stride: _Optional[int] = ..., fields: _Optional[_Iterable[_Union[_PackedElementField_pb2.PackedElementField, _Mapping]]] = ..., data: _Optional[bytes] = ...) -> None: ...
