from foxglove import Color_pb2 as _Color_pb2
from foxglove import Point3_pb2 as _Point3_pb2
from foxglove import Pose_pb2 as _Pose_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TriangleListPrimitive(_message.Message):
    __slots__ = ("pose", "points", "color", "colors", "indices")
    POSE_FIELD_NUMBER: _ClassVar[int]
    POINTS_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    COLORS_FIELD_NUMBER: _ClassVar[int]
    INDICES_FIELD_NUMBER: _ClassVar[int]
    pose: _Pose_pb2.Pose
    points: _containers.RepeatedCompositeFieldContainer[_Point3_pb2.Point3]
    color: _Color_pb2.Color
    colors: _containers.RepeatedCompositeFieldContainer[_Color_pb2.Color]
    indices: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, pose: _Optional[_Union[_Pose_pb2.Pose, _Mapping]] = ..., points: _Optional[_Iterable[_Union[_Point3_pb2.Point3, _Mapping]]] = ..., color: _Optional[_Union[_Color_pb2.Color, _Mapping]] = ..., colors: _Optional[_Iterable[_Union[_Color_pb2.Color, _Mapping]]] = ..., indices: _Optional[_Iterable[int]] = ...) -> None: ...
