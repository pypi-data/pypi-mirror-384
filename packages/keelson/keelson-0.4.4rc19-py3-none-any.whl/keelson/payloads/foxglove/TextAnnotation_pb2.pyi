from foxglove import Color_pb2 as _Color_pb2
from foxglove import Point2_pb2 as _Point2_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TextAnnotation(_message.Message):
    __slots__ = ("timestamp", "position", "text", "font_size", "text_color", "background_color")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    FONT_SIZE_FIELD_NUMBER: _ClassVar[int]
    TEXT_COLOR_FIELD_NUMBER: _ClassVar[int]
    BACKGROUND_COLOR_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    position: _Point2_pb2.Point2
    text: str
    font_size: float
    text_color: _Color_pb2.Color
    background_color: _Color_pb2.Color
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., position: _Optional[_Union[_Point2_pb2.Point2, _Mapping]] = ..., text: _Optional[str] = ..., font_size: _Optional[float] = ..., text_color: _Optional[_Union[_Color_pb2.Color, _Mapping]] = ..., background_color: _Optional[_Union[_Color_pb2.Color, _Mapping]] = ...) -> None: ...
