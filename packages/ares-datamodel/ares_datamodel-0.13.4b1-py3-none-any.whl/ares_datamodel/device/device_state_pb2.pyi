import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
import ares_struct_pb2 as _ares_struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceState(_message.Message):
    __slots__ = ("device_id", "timestamp", "data")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    timestamp: _timestamp_pb2.Timestamp
    data: _ares_struct_pb2.AresStruct
    def __init__(self, device_id: _Optional[str] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., data: _Optional[_Union[_ares_struct_pb2.AresStruct, _Mapping]] = ...) -> None: ...
