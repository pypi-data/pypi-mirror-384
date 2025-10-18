from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class AresUserType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AresAdmin: _ClassVar[AresUserType]
    AresUser: _ClassVar[AresUserType]
AresAdmin: AresUserType
AresUser: AresUserType
