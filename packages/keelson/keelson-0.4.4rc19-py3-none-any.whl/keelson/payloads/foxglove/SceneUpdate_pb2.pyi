from foxglove import SceneEntity_pb2 as _SceneEntity_pb2
from foxglove import SceneEntityDeletion_pb2 as _SceneEntityDeletion_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SceneUpdate(_message.Message):
    __slots__ = ("deletions", "entities")
    DELETIONS_FIELD_NUMBER: _ClassVar[int]
    ENTITIES_FIELD_NUMBER: _ClassVar[int]
    deletions: _containers.RepeatedCompositeFieldContainer[_SceneEntityDeletion_pb2.SceneEntityDeletion]
    entities: _containers.RepeatedCompositeFieldContainer[_SceneEntity_pb2.SceneEntity]
    def __init__(self, deletions: _Optional[_Iterable[_Union[_SceneEntityDeletion_pb2.SceneEntityDeletion, _Mapping]]] = ..., entities: _Optional[_Iterable[_Union[_SceneEntity_pb2.SceneEntity, _Mapping]]] = ...) -> None: ...
