from foxglove import Color_pb2 as _Color_pb2
from foxglove import Pose_pb2 as _Pose_pb2
from foxglove import Vector3_pb2 as _Vector3_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CylinderPrimitive(_message.Message):
    __slots__ = ("pose", "size", "bottom_scale", "top_scale", "color")
    POSE_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    BOTTOM_SCALE_FIELD_NUMBER: _ClassVar[int]
    TOP_SCALE_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    pose: _Pose_pb2.Pose
    size: _Vector3_pb2.Vector3
    bottom_scale: float
    top_scale: float
    color: _Color_pb2.Color
    def __init__(self, pose: _Optional[_Union[_Pose_pb2.Pose, _Mapping]] = ..., size: _Optional[_Union[_Vector3_pb2.Vector3, _Mapping]] = ..., bottom_scale: _Optional[float] = ..., top_scale: _Optional[float] = ..., color: _Optional[_Union[_Color_pb2.Color, _Mapping]] = ...) -> None: ...
