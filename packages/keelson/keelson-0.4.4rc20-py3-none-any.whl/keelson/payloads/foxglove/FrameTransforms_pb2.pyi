from foxglove import FrameTransform_pb2 as _FrameTransform_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class FrameTransforms(_message.Message):
    __slots__ = ("transforms",)
    TRANSFORMS_FIELD_NUMBER: _ClassVar[int]
    transforms: _containers.RepeatedCompositeFieldContainer[_FrameTransform_pb2.FrameTransform]
    def __init__(self, transforms: _Optional[_Iterable[_Union[_FrameTransform_pb2.FrameTransform, _Mapping]]] = ...) -> None: ...
