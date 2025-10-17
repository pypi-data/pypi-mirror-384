from foxglove import Color_pb2 as _Color_pb2
from foxglove import Point2_pb2 as _Point2_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CircleAnnotation(_message.Message):
    __slots__ = ("timestamp", "position", "diameter", "thickness", "fill_color", "outline_color")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    DIAMETER_FIELD_NUMBER: _ClassVar[int]
    THICKNESS_FIELD_NUMBER: _ClassVar[int]
    FILL_COLOR_FIELD_NUMBER: _ClassVar[int]
    OUTLINE_COLOR_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    position: _Point2_pb2.Point2
    diameter: float
    thickness: float
    fill_color: _Color_pb2.Color
    outline_color: _Color_pb2.Color
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., position: _Optional[_Union[_Point2_pb2.Point2, _Mapping]] = ..., diameter: _Optional[float] = ..., thickness: _Optional[float] = ..., fill_color: _Optional[_Union[_Color_pb2.Color, _Mapping]] = ..., outline_color: _Optional[_Union[_Color_pb2.Color, _Mapping]] = ...) -> None: ...
