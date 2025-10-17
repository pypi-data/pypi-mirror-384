from foxglove import ArrowPrimitive_pb2 as _ArrowPrimitive_pb2
from foxglove import CubePrimitive_pb2 as _CubePrimitive_pb2
from foxglove import CylinderPrimitive_pb2 as _CylinderPrimitive_pb2
from foxglove import KeyValuePair_pb2 as _KeyValuePair_pb2
from foxglove import LinePrimitive_pb2 as _LinePrimitive_pb2
from foxglove import ModelPrimitive_pb2 as _ModelPrimitive_pb2
from foxglove import SpherePrimitive_pb2 as _SpherePrimitive_pb2
from foxglove import TextPrimitive_pb2 as _TextPrimitive_pb2
from foxglove import TriangleListPrimitive_pb2 as _TriangleListPrimitive_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SceneEntity(_message.Message):
    __slots__ = ("timestamp", "frame_id", "id", "lifetime", "frame_locked", "metadata", "arrows", "cubes", "spheres", "cylinders", "lines", "triangles", "texts", "models")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    LIFETIME_FIELD_NUMBER: _ClassVar[int]
    FRAME_LOCKED_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ARROWS_FIELD_NUMBER: _ClassVar[int]
    CUBES_FIELD_NUMBER: _ClassVar[int]
    SPHERES_FIELD_NUMBER: _ClassVar[int]
    CYLINDERS_FIELD_NUMBER: _ClassVar[int]
    LINES_FIELD_NUMBER: _ClassVar[int]
    TRIANGLES_FIELD_NUMBER: _ClassVar[int]
    TEXTS_FIELD_NUMBER: _ClassVar[int]
    MODELS_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    frame_id: str
    id: str
    lifetime: _duration_pb2.Duration
    frame_locked: bool
    metadata: _containers.RepeatedCompositeFieldContainer[_KeyValuePair_pb2.KeyValuePair]
    arrows: _containers.RepeatedCompositeFieldContainer[_ArrowPrimitive_pb2.ArrowPrimitive]
    cubes: _containers.RepeatedCompositeFieldContainer[_CubePrimitive_pb2.CubePrimitive]
    spheres: _containers.RepeatedCompositeFieldContainer[_SpherePrimitive_pb2.SpherePrimitive]
    cylinders: _containers.RepeatedCompositeFieldContainer[_CylinderPrimitive_pb2.CylinderPrimitive]
    lines: _containers.RepeatedCompositeFieldContainer[_LinePrimitive_pb2.LinePrimitive]
    triangles: _containers.RepeatedCompositeFieldContainer[_TriangleListPrimitive_pb2.TriangleListPrimitive]
    texts: _containers.RepeatedCompositeFieldContainer[_TextPrimitive_pb2.TextPrimitive]
    models: _containers.RepeatedCompositeFieldContainer[_ModelPrimitive_pb2.ModelPrimitive]
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., frame_id: _Optional[str] = ..., id: _Optional[str] = ..., lifetime: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., frame_locked: bool = ..., metadata: _Optional[_Iterable[_Union[_KeyValuePair_pb2.KeyValuePair, _Mapping]]] = ..., arrows: _Optional[_Iterable[_Union[_ArrowPrimitive_pb2.ArrowPrimitive, _Mapping]]] = ..., cubes: _Optional[_Iterable[_Union[_CubePrimitive_pb2.CubePrimitive, _Mapping]]] = ..., spheres: _Optional[_Iterable[_Union[_SpherePrimitive_pb2.SpherePrimitive, _Mapping]]] = ..., cylinders: _Optional[_Iterable[_Union[_CylinderPrimitive_pb2.CylinderPrimitive, _Mapping]]] = ..., lines: _Optional[_Iterable[_Union[_LinePrimitive_pb2.LinePrimitive, _Mapping]]] = ..., triangles: _Optional[_Iterable[_Union[_TriangleListPrimitive_pb2.TriangleListPrimitive, _Mapping]]] = ..., texts: _Optional[_Iterable[_Union[_TextPrimitive_pb2.TextPrimitive, _Mapping]]] = ..., models: _Optional[_Iterable[_Union[_ModelPrimitive_pb2.ModelPrimitive, _Mapping]]] = ...) -> None: ...
