from foxglove import Color_pb2 as _Color_pb2
from foxglove import Pose_pb2 as _Pose_pb2
from foxglove import Vector3_pb2 as _Vector3_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CubePrimitive(_message.Message):
    __slots__ = ("pose", "size", "color")
    POSE_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    pose: _Pose_pb2.Pose
    size: _Vector3_pb2.Vector3
    color: _Color_pb2.Color
    def __init__(self, pose: _Optional[_Union[_Pose_pb2.Pose, _Mapping]] = ..., size: _Optional[_Union[_Vector3_pb2.Vector3, _Mapping]] = ..., color: _Optional[_Union[_Color_pb2.Color, _Mapping]] = ...) -> None: ...
