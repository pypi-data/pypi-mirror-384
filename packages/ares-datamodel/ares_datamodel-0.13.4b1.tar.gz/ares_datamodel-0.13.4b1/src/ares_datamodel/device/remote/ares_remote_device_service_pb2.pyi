import ares_struct_pb2 as _ares_struct_pb2
from device import device_status_pb2 as _device_status_pb2
from google.protobuf import empty_pb2 as _empty_pb2
import ares_data_schema_pb2 as _ares_data_schema_pb2
from device import device_command_descriptor_pb2 as _device_command_descriptor_pb2
from device import device_execution_result_pb2 as _device_execution_result_pb2
from device import device_polling_settings_pb2 as _device_polling_settings_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceInfoResponse(_message.Message):
    __slots__ = ("name", "version", "description")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    version: str
    description: str
    def __init__(self, name: _Optional[str] = ..., version: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class SettingsSchemaResponse(_message.Message):
    __slots__ = ("schema",)
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    schema: _ares_data_schema_pb2.AresDataSchema
    def __init__(self, schema: _Optional[_Union[_ares_data_schema_pb2.AresDataSchema, _Mapping]] = ...) -> None: ...

class CurrentSettingsResponse(_message.Message):
    __slots__ = ("settings",)
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    settings: _ares_struct_pb2.AresStruct
    def __init__(self, settings: _Optional[_Union[_ares_struct_pb2.AresStruct, _Mapping]] = ...) -> None: ...

class SetSettingsRequest(_message.Message):
    __slots__ = ("settings",)
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    settings: _ares_struct_pb2.AresStruct
    def __init__(self, settings: _Optional[_Union[_ares_struct_pb2.AresStruct, _Mapping]] = ...) -> None: ...

class CommandsResponse(_message.Message):
    __slots__ = ("commands",)
    COMMANDS_FIELD_NUMBER: _ClassVar[int]
    commands: _containers.RepeatedCompositeFieldContainer[_device_command_descriptor_pb2.DeviceCommandDescriptor]
    def __init__(self, commands: _Optional[_Iterable[_Union[_device_command_descriptor_pb2.DeviceCommandDescriptor, _Mapping]]] = ...) -> None: ...

class DeviceStateStreamRequest(_message.Message):
    __slots__ = ("polling_settings",)
    POLLING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    polling_settings: _device_polling_settings_pb2.DevicePollingSettings
    def __init__(self, polling_settings: _Optional[_Union[_device_polling_settings_pb2.DevicePollingSettings, _Mapping]] = ...) -> None: ...

class StateSchemaResponse(_message.Message):
    __slots__ = ("schema",)
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    schema: _ares_data_schema_pb2.AresDataSchema
    def __init__(self, schema: _Optional[_Union[_ares_data_schema_pb2.AresDataSchema, _Mapping]] = ...) -> None: ...

class DeviceStateResponse(_message.Message):
    __slots__ = ("state",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: _ares_struct_pb2.AresStruct
    def __init__(self, state: _Optional[_Union[_ares_struct_pb2.AresStruct, _Mapping]] = ...) -> None: ...

class ExecuteCommandRequest(_message.Message):
    __slots__ = ("command_name", "arguments")
    COMMAND_NAME_FIELD_NUMBER: _ClassVar[int]
    ARGUMENTS_FIELD_NUMBER: _ClassVar[int]
    command_name: str
    arguments: _ares_struct_pb2.AresStruct
    def __init__(self, command_name: _Optional[str] = ..., arguments: _Optional[_Union[_ares_struct_pb2.AresStruct, _Mapping]] = ...) -> None: ...
