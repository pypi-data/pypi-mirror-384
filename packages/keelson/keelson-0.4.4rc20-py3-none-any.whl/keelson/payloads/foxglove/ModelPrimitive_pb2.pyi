from foxglove import Color_pb2 as _Color_pb2
from foxglove import Pose_pb2 as _Pose_pb2
from foxglove import Vector3_pb2 as _Vector3_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ModelPrimitive(_message.Message):
    __slots__ = ("pose", "scale", "color", "override_color", "url", "media_type", "data")
    POSE_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    OVERRIDE_COLOR_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    MEDIA_TYPE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    pose: _Pose_pb2.Pose
    scale: _Vector3_pb2.Vector3
    color: _Color_pb2.Color
    override_color: bool
    url: str
    media_type: str
    data: bytes
    def __init__(self, pose: _Optional[_Union[_Pose_pb2.Pose, _Mapping]] = ..., scale: _Optional[_Union[_Vector3_pb2.Vector3, _Mapping]] = ..., color: _Optional[_Union[_Color_pb2.Color, _Mapping]] = ..., override_color: bool = ..., url: _Optional[str] = ..., media_type: _Optional[str] = ..., data: _Optional[bytes] = ...) -> None: ...
