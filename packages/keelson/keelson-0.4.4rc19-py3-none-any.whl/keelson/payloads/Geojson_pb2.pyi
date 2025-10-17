from google.protobuf import timestamp_pb2 as _timestamp_pb2
from foxglove import GeoJSON_pb2 as _GeoJSON_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TimestampedGeoJSON(_message.Message):
    __slots__ = ("timestamp", "geojson")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    GEOJSON_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    geojson: _GeoJSON_pb2.GeoJSON
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., geojson: _Optional[_Union[_GeoJSON_pb2.GeoJSON, _Mapping]] = ...) -> None: ...
