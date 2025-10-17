from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ROCStatus(_message.Message):
    __slots__ = ("timestamp", "entities")
    class ROCEntity(_message.Message):
        __slots__ = ("entity_id", "state")
        class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            UNKNOWN: _ClassVar[ROCStatus.ROCEntity.State]
            UNASSIGNED: _ClassVar[ROCStatus.ROCEntity.State]
            MONITORING: _ClassVar[ROCStatus.ROCEntity.State]
            CONTROLLING: _ClassVar[ROCStatus.ROCEntity.State]
        UNKNOWN: ROCStatus.ROCEntity.State
        UNASSIGNED: ROCStatus.ROCEntity.State
        MONITORING: ROCStatus.ROCEntity.State
        CONTROLLING: ROCStatus.ROCEntity.State
        ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
        STATE_FIELD_NUMBER: _ClassVar[int]
        entity_id: str
        state: ROCStatus.ROCEntity.State
        def __init__(self, entity_id: _Optional[str] = ..., state: _Optional[_Union[ROCStatus.ROCEntity.State, str]] = ...) -> None: ...
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ENTITIES_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    entities: _containers.RepeatedCompositeFieldContainer[ROCStatus.ROCEntity]
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., entities: _Optional[_Iterable[_Union[ROCStatus.ROCEntity, _Mapping]]] = ...) -> None: ...
