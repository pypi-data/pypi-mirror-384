from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PollingType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[PollingType]
    INTERVAL: _ClassVar[PollingType]
    ON_CHANGE: _ClassVar[PollingType]
NONE: PollingType
INTERVAL: PollingType
ON_CHANGE: PollingType

class DevicePollingSettings(_message.Message):
    __slots__ = ("device_id", "polling_type", "interval_ms")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    POLLING_TYPE_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_MS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    polling_type: PollingType
    interval_ms: int
    def __init__(self, device_id: _Optional[str] = ..., polling_type: _Optional[_Union[PollingType, str]] = ..., interval_ms: _Optional[int] = ...) -> None: ...
