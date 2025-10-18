from device import device_state_request_filter_pb2 as _device_state_request_filter_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExportType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNSPECIFIED: _ClassVar[ExportType]
    COMBINED: _ClassVar[ExportType]
    ZIPPED: _ClassVar[ExportType]
UNSPECIFIED: ExportType
COMBINED: ExportType
ZIPPED: ExportType

class DeviceStateRequest(_message.Message):
    __slots__ = ("filter", "export_type")
    FILTER_FIELD_NUMBER: _ClassVar[int]
    EXPORT_TYPE_FIELD_NUMBER: _ClassVar[int]
    filter: _device_state_request_filter_pb2.DeviceStateRequestFilter
    export_type: ExportType
    def __init__(self, filter: _Optional[_Union[_device_state_request_filter_pb2.DeviceStateRequestFilter, _Mapping]] = ..., export_type: _Optional[_Union[ExportType, str]] = ...) -> None: ...

class DeviceStateResponse(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    def __init__(self, data: _Optional[bytes] = ...) -> None: ...
