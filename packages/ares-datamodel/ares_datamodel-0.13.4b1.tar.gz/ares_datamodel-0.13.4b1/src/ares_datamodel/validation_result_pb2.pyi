from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ValidationResult(_message.Message):
    __slots__ = ("success", "messages")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    success: bool
    messages: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, success: bool = ..., messages: _Optional[_Iterable[str]] = ...) -> None: ...
