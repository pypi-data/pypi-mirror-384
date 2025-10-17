from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LocationFixQuality(_message.Message):
    __slots__ = ("timestamp", "fix_type")
    class FixType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[LocationFixQuality.FixType]
        INVALID: _ClassVar[LocationFixQuality.FixType]
        FIX_NO: _ClassVar[LocationFixQuality.FixType]
        FIX_2D: _ClassVar[LocationFixQuality.FixType]
        FIX_3D: _ClassVar[LocationFixQuality.FixType]
        GPS_DR: _ClassVar[LocationFixQuality.FixType]
        TIME_ONLY: _ClassVar[LocationFixQuality.FixType]
        DR_ONLY: _ClassVar[LocationFixQuality.FixType]
        FIX_3D_DGPS: _ClassVar[LocationFixQuality.FixType]
        FIX_3D_RTK: _ClassVar[LocationFixQuality.FixType]
    UNKNOWN: LocationFixQuality.FixType
    INVALID: LocationFixQuality.FixType
    FIX_NO: LocationFixQuality.FixType
    FIX_2D: LocationFixQuality.FixType
    FIX_3D: LocationFixQuality.FixType
    GPS_DR: LocationFixQuality.FixType
    TIME_ONLY: LocationFixQuality.FixType
    DR_ONLY: LocationFixQuality.FixType
    FIX_3D_DGPS: LocationFixQuality.FixType
    FIX_3D_RTK: LocationFixQuality.FixType
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    FIX_TYPE_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    fix_type: LocationFixQuality.FixType
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., fix_type: _Optional[_Union[LocationFixQuality.FixType, str]] = ...) -> None: ...
