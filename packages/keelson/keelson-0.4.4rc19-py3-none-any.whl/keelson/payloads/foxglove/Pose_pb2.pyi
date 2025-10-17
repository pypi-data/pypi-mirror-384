from foxglove import Quaternion_pb2 as _Quaternion_pb2
from foxglove import Vector3_pb2 as _Vector3_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Pose(_message.Message):
    __slots__ = ("position", "orientation")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    position: _Vector3_pb2.Vector3
    orientation: _Quaternion_pb2.Quaternion
    def __init__(self, position: _Optional[_Union[_Vector3_pb2.Vector3, _Mapping]] = ..., orientation: _Optional[_Union[_Quaternion_pb2.Quaternion, _Mapping]] = ...) -> None: ...
