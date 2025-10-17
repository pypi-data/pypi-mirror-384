from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class VesselNavStatus(_message.Message):
    __slots__ = ("timestamp", "navigation_status")
    class NavigationStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[VesselNavStatus.NavigationStatus]
        UNDER_WAY: _ClassVar[VesselNavStatus.NavigationStatus]
        AT_ANCHOR: _ClassVar[VesselNavStatus.NavigationStatus]
        NOT_UNDER_COMMAND: _ClassVar[VesselNavStatus.NavigationStatus]
        RESTRICTED_MANEUVERABILITY: _ClassVar[VesselNavStatus.NavigationStatus]
        CONSTRAINED_BY_DRAFT: _ClassVar[VesselNavStatus.NavigationStatus]
        MOORING: _ClassVar[VesselNavStatus.NavigationStatus]
        AGROUND: _ClassVar[VesselNavStatus.NavigationStatus]
        FISHING: _ClassVar[VesselNavStatus.NavigationStatus]
        UNDER_WAY_SAILING: _ClassVar[VesselNavStatus.NavigationStatus]
        HSC: _ClassVar[VesselNavStatus.NavigationStatus]
        WIG: _ClassVar[VesselNavStatus.NavigationStatus]
        RESERVED_12: _ClassVar[VesselNavStatus.NavigationStatus]
        RESERVED_13: _ClassVar[VesselNavStatus.NavigationStatus]
        RESERVED_14: _ClassVar[VesselNavStatus.NavigationStatus]
        AIS_SART: _ClassVar[VesselNavStatus.NavigationStatus]
        NOT_DEFINED: _ClassVar[VesselNavStatus.NavigationStatus]
    UNKNOWN: VesselNavStatus.NavigationStatus
    UNDER_WAY: VesselNavStatus.NavigationStatus
    AT_ANCHOR: VesselNavStatus.NavigationStatus
    NOT_UNDER_COMMAND: VesselNavStatus.NavigationStatus
    RESTRICTED_MANEUVERABILITY: VesselNavStatus.NavigationStatus
    CONSTRAINED_BY_DRAFT: VesselNavStatus.NavigationStatus
    MOORING: VesselNavStatus.NavigationStatus
    AGROUND: VesselNavStatus.NavigationStatus
    FISHING: VesselNavStatus.NavigationStatus
    UNDER_WAY_SAILING: VesselNavStatus.NavigationStatus
    HSC: VesselNavStatus.NavigationStatus
    WIG: VesselNavStatus.NavigationStatus
    RESERVED_12: VesselNavStatus.NavigationStatus
    RESERVED_13: VesselNavStatus.NavigationStatus
    RESERVED_14: VesselNavStatus.NavigationStatus
    AIS_SART: VesselNavStatus.NavigationStatus
    NOT_DEFINED: VesselNavStatus.NavigationStatus
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    NAVIGATION_STATUS_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    navigation_status: VesselNavStatus.NavigationStatus
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., navigation_status: _Optional[_Union[VesselNavStatus.NavigationStatus, str]] = ...) -> None: ...
