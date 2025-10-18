from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceLoggingSettings(_message.Message):
    __slots__ = ("device_id", "logging_type", "interval_ms", "deltas")
    class LoggingType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NONE: _ClassVar[DeviceLoggingSettings.LoggingType]
        INTERVAL: _ClassVar[DeviceLoggingSettings.LoggingType]
        ON_CHANGE: _ClassVar[DeviceLoggingSettings.LoggingType]
    NONE: DeviceLoggingSettings.LoggingType
    INTERVAL: DeviceLoggingSettings.LoggingType
    ON_CHANGE: DeviceLoggingSettings.LoggingType
    class DeltasEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    LOGGING_TYPE_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_MS_FIELD_NUMBER: _ClassVar[int]
    DELTAS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    logging_type: DeviceLoggingSettings.LoggingType
    interval_ms: int
    deltas: _containers.ScalarMap[str, float]
    def __init__(self, device_id: _Optional[str] = ..., logging_type: _Optional[_Union[DeviceLoggingSettings.LoggingType, str]] = ..., interval_ms: _Optional[int] = ..., deltas: _Optional[_Mapping[str, float]] = ...) -> None: ...
