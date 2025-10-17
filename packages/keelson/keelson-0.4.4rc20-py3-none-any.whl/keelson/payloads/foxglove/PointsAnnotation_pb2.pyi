from foxglove import Color_pb2 as _Color_pb2
from foxglove import Point2_pb2 as _Point2_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PointsAnnotation(_message.Message):
    __slots__ = ("timestamp", "type", "points", "outline_color", "outline_colors", "fill_color", "thickness")
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[PointsAnnotation.Type]
        POINTS: _ClassVar[PointsAnnotation.Type]
        LINE_LOOP: _ClassVar[PointsAnnotation.Type]
        LINE_STRIP: _ClassVar[PointsAnnotation.Type]
        LINE_LIST: _ClassVar[PointsAnnotation.Type]
    UNKNOWN: PointsAnnotation.Type
    POINTS: PointsAnnotation.Type
    LINE_LOOP: PointsAnnotation.Type
    LINE_STRIP: PointsAnnotation.Type
    LINE_LIST: PointsAnnotation.Type
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    POINTS_FIELD_NUMBER: _ClassVar[int]
    OUTLINE_COLOR_FIELD_NUMBER: _ClassVar[int]
    OUTLINE_COLORS_FIELD_NUMBER: _ClassVar[int]
    FILL_COLOR_FIELD_NUMBER: _ClassVar[int]
    THICKNESS_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    type: PointsAnnotation.Type
    points: _containers.RepeatedCompositeFieldContainer[_Point2_pb2.Point2]
    outline_color: _Color_pb2.Color
    outline_colors: _containers.RepeatedCompositeFieldContainer[_Color_pb2.Color]
    fill_color: _Color_pb2.Color
    thickness: float
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., type: _Optional[_Union[PointsAnnotation.Type, str]] = ..., points: _Optional[_Iterable[_Union[_Point2_pb2.Point2, _Mapping]]] = ..., outline_color: _Optional[_Union[_Color_pb2.Color, _Mapping]] = ..., outline_colors: _Optional[_Iterable[_Union[_Color_pb2.Color, _Mapping]]] = ..., fill_color: _Optional[_Union[_Color_pb2.Color, _Mapping]] = ..., thickness: _Optional[float] = ...) -> None: ...
