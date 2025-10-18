import ares_data_schema_pb2 as _ares_data_schema_pb2
from device import device_command_descriptor_pb2 as _device_command_descriptor_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceInfo(_message.Message):
    __slots__ = ("unique_id", "name", "type", "description", "version", "url", "settings_schema", "commands")
    UNIQUE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    COMMANDS_FIELD_NUMBER: _ClassVar[int]
    unique_id: str
    name: str
    type: str
    description: str
    version: str
    url: str
    settings_schema: _ares_data_schema_pb2.AresDataSchema
    commands: _containers.RepeatedCompositeFieldContainer[_device_command_descriptor_pb2.DeviceCommandDescriptor]
    def __init__(self, unique_id: _Optional[str] = ..., name: _Optional[str] = ..., type: _Optional[str] = ..., description: _Optional[str] = ..., version: _Optional[str] = ..., url: _Optional[str] = ..., settings_schema: _Optional[_Union[_ares_data_schema_pb2.AresDataSchema, _Mapping]] = ..., commands: _Optional[_Iterable[_Union[_device_command_descriptor_pb2.DeviceCommandDescriptor, _Mapping]]] = ...) -> None: ...
