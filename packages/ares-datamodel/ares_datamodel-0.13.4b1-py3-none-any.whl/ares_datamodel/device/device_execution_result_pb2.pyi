import ares_struct_pb2 as _ares_struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceExecutionResult(_message.Message):
    __slots__ = ("result", "success", "error")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    result: _ares_struct_pb2.AresStruct
    success: bool
    error: str
    def __init__(self, result: _Optional[_Union[_ares_struct_pb2.AresStruct, _Mapping]] = ..., success: bool = ..., error: _Optional[str] = ...) -> None: ...
