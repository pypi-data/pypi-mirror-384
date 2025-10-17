from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Audio(_message.Message):
    __slots__ = ("timestamp", "text_to_voice", "data", "encoding")
    class Encoding(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        MP3: _ClassVar[Audio.Encoding]
        WAV: _ClassVar[Audio.Encoding]
    MP3: Audio.Encoding
    WAV: Audio.Encoding
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TEXT_TO_VOICE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    ENCODING_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    text_to_voice: str
    data: bytes
    encoding: Audio.Encoding
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., text_to_voice: _Optional[str] = ..., data: _Optional[bytes] = ..., encoding: _Optional[_Union[Audio.Encoding, str]] = ...) -> None: ...
