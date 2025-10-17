from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TargetType(_message.Message):
    __slots__ = ("timestamp", "type")
    class TargetTypes(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[TargetType.TargetTypes]
        PERSON: _ClassVar[TargetType.TargetTypes]
        VESSEL: _ClassVar[TargetType.TargetTypes]
        SEAMARK: _ClassVar[TargetType.TargetTypes]
    UNKNOWN: TargetType.TargetTypes
    PERSON: TargetType.TargetTypes
    VESSEL: TargetType.TargetTypes
    SEAMARK: TargetType.TargetTypes
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    type: TargetType.TargetTypes
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., type: _Optional[_Union[TargetType.TargetTypes, str]] = ...) -> None: ...
