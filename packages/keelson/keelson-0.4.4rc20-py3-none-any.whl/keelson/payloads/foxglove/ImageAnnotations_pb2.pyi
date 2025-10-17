from foxglove import CircleAnnotation_pb2 as _CircleAnnotation_pb2
from foxglove import PointsAnnotation_pb2 as _PointsAnnotation_pb2
from foxglove import TextAnnotation_pb2 as _TextAnnotation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ImageAnnotations(_message.Message):
    __slots__ = ("circles", "points", "texts")
    CIRCLES_FIELD_NUMBER: _ClassVar[int]
    POINTS_FIELD_NUMBER: _ClassVar[int]
    TEXTS_FIELD_NUMBER: _ClassVar[int]
    circles: _containers.RepeatedCompositeFieldContainer[_CircleAnnotation_pb2.CircleAnnotation]
    points: _containers.RepeatedCompositeFieldContainer[_PointsAnnotation_pb2.PointsAnnotation]
    texts: _containers.RepeatedCompositeFieldContainer[_TextAnnotation_pb2.TextAnnotation]
    def __init__(self, circles: _Optional[_Iterable[_Union[_CircleAnnotation_pb2.CircleAnnotation, _Mapping]]] = ..., points: _Optional[_Iterable[_Union[_PointsAnnotation_pb2.PointsAnnotation, _Mapping]]] = ..., texts: _Optional[_Iterable[_Union[_TextAnnotation_pb2.TextAnnotation, _Mapping]]] = ...) -> None: ...
