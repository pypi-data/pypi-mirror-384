from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SensorStatus(_message.Message):
    __slots__ = ("timestamp", "mode")
    class OperatingMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[SensorStatus.OperatingMode]
        RUNNING: _ClassVar[SensorStatus.OperatingMode]
        STANDBY: _ClassVar[SensorStatus.OperatingMode]
        DISABLED: _ClassVar[SensorStatus.OperatingMode]
        OFF: _ClassVar[SensorStatus.OperatingMode]
        ERROR: _ClassVar[SensorStatus.OperatingMode]
    UNKNOWN: SensorStatus.OperatingMode
    RUNNING: SensorStatus.OperatingMode
    STANDBY: SensorStatus.OperatingMode
    DISABLED: SensorStatus.OperatingMode
    OFF: SensorStatus.OperatingMode
    ERROR: SensorStatus.OperatingMode
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    mode: SensorStatus.OperatingMode
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., mode: _Optional[_Union[SensorStatus.OperatingMode, str]] = ...) -> None: ...
