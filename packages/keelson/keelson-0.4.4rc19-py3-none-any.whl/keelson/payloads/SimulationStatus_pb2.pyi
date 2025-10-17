from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SimulationStatus(_message.Message):
    __slots__ = ("timestamp", "state", "name", "id", "timestampSimulation")
    class SimulationState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[SimulationStatus.SimulationState]
        STOPPED: _ClassVar[SimulationStatus.SimulationState]
        ASSIGNED: _ClassVar[SimulationStatus.SimulationState]
        RUNNING: _ClassVar[SimulationStatus.SimulationState]
        PAUSED: _ClassVar[SimulationStatus.SimulationState]
    UNKNOWN: SimulationStatus.SimulationState
    STOPPED: SimulationStatus.SimulationState
    ASSIGNED: SimulationStatus.SimulationState
    RUNNING: SimulationStatus.SimulationState
    PAUSED: SimulationStatus.SimulationState
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMPSIMULATION_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    state: SimulationStatus.SimulationState
    name: str
    id: str
    timestampSimulation: _timestamp_pb2.Timestamp
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., state: _Optional[_Union[SimulationStatus.SimulationState, str]] = ..., name: _Optional[str] = ..., id: _Optional[str] = ..., timestampSimulation: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
