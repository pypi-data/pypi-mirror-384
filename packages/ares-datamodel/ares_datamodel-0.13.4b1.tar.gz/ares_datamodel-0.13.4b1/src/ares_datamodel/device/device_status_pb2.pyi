from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OperationalState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNSPECIFIED: _ClassVar[OperationalState]
    INACTIVE: _ClassVar[OperationalState]
    ACTIVE: _ClassVar[OperationalState]
    ERROR: _ClassVar[OperationalState]
UNSPECIFIED: OperationalState
INACTIVE: OperationalState
ACTIVE: OperationalState
ERROR: OperationalState

class DeviceOperationalStatus(_message.Message):
    __slots__ = ("operational_state", "message")
    OPERATIONAL_STATE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    operational_state: OperationalState
    message: str
    def __init__(self, operational_state: _Optional[_Union[OperationalState, str]] = ..., message: _Optional[str] = ...) -> None: ...
