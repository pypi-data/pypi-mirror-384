from google.protobuf import empty_pb2 as _empty_pb2
from templates import command_metadata_pb2 as _command_metadata_pb2
from templates import command_template_pb2 as _command_template_pb2
from device import device_execution_result_pb2 as _device_execution_result_pb2
from device import remote_device_config_pb2 as _remote_device_config_pb2
from device import device_status_pb2 as _device_status_pb2
from device import device_info_pb2 as _device_info_pb2
from device import device_config_pb2 as _device_config_pb2
from device import device_settings_pb2 as _device_settings_pb2
from device import device_polling_settings_pb2 as _device_polling_settings_pb2
import ares_struct_pb2 as _ares_struct_pb2
import ares_data_schema_pb2 as _ares_data_schema_pb2
from device import device_logging_settings_pb2 as _device_logging_settings_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ListAresDevicesResponse(_message.Message):
    __slots__ = ("ares_devices",)
    ARES_DEVICES_FIELD_NUMBER: _ClassVar[int]
    ares_devices: _containers.RepeatedCompositeFieldContainer[_device_info_pb2.DeviceInfo]
    def __init__(self, ares_devices: _Optional[_Iterable[_Union[_device_info_pb2.DeviceInfo, _Mapping]]] = ...) -> None: ...

class ListAresRemoteDevicesResponse(_message.Message):
    __slots__ = ("devices",)
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    devices: _containers.RepeatedCompositeFieldContainer[_device_info_pb2.DeviceInfo]
    def __init__(self, devices: _Optional[_Iterable[_Union[_device_info_pb2.DeviceInfo, _Mapping]]] = ...) -> None: ...

class ListServerSerialPortsResponse(_message.Message):
    __slots__ = ("serial_ports",)
    SERIAL_PORTS_FIELD_NUMBER: _ClassVar[int]
    serial_ports: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, serial_ports: _Optional[_Iterable[str]] = ...) -> None: ...

class CommandMetadatasRequest(_message.Message):
    __slots__ = ("device_id",)
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    def __init__(self, device_id: _Optional[str] = ...) -> None: ...

class CommandMetadatasResponse(_message.Message):
    __slots__ = ("metadatas",)
    METADATAS_FIELD_NUMBER: _ClassVar[int]
    metadatas: _containers.RepeatedCompositeFieldContainer[_command_metadata_pb2.CommandMetadata]
    def __init__(self, metadatas: _Optional[_Iterable[_Union[_command_metadata_pb2.CommandMetadata, _Mapping]]] = ...) -> None: ...

class DeviceStatusRequest(_message.Message):
    __slots__ = ("device_id",)
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    def __init__(self, device_id: _Optional[str] = ...) -> None: ...

class DeviceStateStreamRequest(_message.Message):
    __slots__ = ("device_id", "polling_settings")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    POLLING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    polling_settings: _device_polling_settings_pb2.DevicePollingSettings
    def __init__(self, device_id: _Optional[str] = ..., polling_settings: _Optional[_Union[_device_polling_settings_pb2.DevicePollingSettings, _Mapping]] = ...) -> None: ...

class DeviceStateRequest(_message.Message):
    __slots__ = ("device_id",)
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    def __init__(self, device_id: _Optional[str] = ...) -> None: ...

class DeviceStateResponse(_message.Message):
    __slots__ = ("state",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: _ares_struct_pb2.AresStruct
    def __init__(self, state: _Optional[_Union[_ares_struct_pb2.AresStruct, _Mapping]] = ...) -> None: ...

class DeviceStateSchemaRequest(_message.Message):
    __slots__ = ("device_id",)
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    def __init__(self, device_id: _Optional[str] = ...) -> None: ...

class DeviceStateSchemaResponse(_message.Message):
    __slots__ = ("schema",)
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    schema: _ares_data_schema_pb2.AresDataSchema
    def __init__(self, schema: _Optional[_Union[_ares_data_schema_pb2.AresDataSchema, _Mapping]] = ...) -> None: ...

class DeviceLoggerSettingsRequest(_message.Message):
    __slots__ = ("device_id",)
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    def __init__(self, device_id: _Optional[str] = ...) -> None: ...

class DeviceLoggersResponse(_message.Message):
    __slots__ = ("loggers",)
    LOGGERS_FIELD_NUMBER: _ClassVar[int]
    loggers: _containers.RepeatedCompositeFieldContainer[_device_logging_settings_pb2.DeviceLoggingSettings]
    def __init__(self, loggers: _Optional[_Iterable[_Union[_device_logging_settings_pb2.DeviceLoggingSettings, _Mapping]]] = ...) -> None: ...

class DeviceInfoRequest(_message.Message):
    __slots__ = ("device_id",)
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    def __init__(self, device_id: _Optional[str] = ...) -> None: ...

class DeviceSettingsRequest(_message.Message):
    __slots__ = ("device_id",)
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    def __init__(self, device_id: _Optional[str] = ...) -> None: ...

class DeviceActivateRequest(_message.Message):
    __slots__ = ("device_id",)
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    def __init__(self, device_id: _Optional[str] = ...) -> None: ...

class DeviceConfigRequest(_message.Message):
    __slots__ = ("device_type",)
    DEVICE_TYPE_FIELD_NUMBER: _ClassVar[int]
    device_type: str
    def __init__(self, device_type: _Optional[str] = ...) -> None: ...

class DeviceConfigResponse(_message.Message):
    __slots__ = ("configs",)
    CONFIGS_FIELD_NUMBER: _ClassVar[int]
    configs: _containers.RepeatedCompositeFieldContainer[_device_config_pb2.DeviceConfig]
    def __init__(self, configs: _Optional[_Iterable[_Union[_device_config_pb2.DeviceConfig, _Mapping]]] = ...) -> None: ...

class RemoteDeviceConfigResponse(_message.Message):
    __slots__ = ("configs",)
    CONFIGS_FIELD_NUMBER: _ClassVar[int]
    configs: _containers.RepeatedCompositeFieldContainer[_remote_device_config_pb2.RemoteDeviceConfig]
    def __init__(self, configs: _Optional[_Iterable[_Union[_remote_device_config_pb2.RemoteDeviceConfig, _Mapping]]] = ...) -> None: ...

class AddRemoteDeviceRequest(_message.Message):
    __slots__ = ("name", "url")
    NAME_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    name: str
    url: str
    def __init__(self, name: _Optional[str] = ..., url: _Optional[str] = ...) -> None: ...

class AddRemoteDeviceResponse(_message.Message):
    __slots__ = ("device_id", "success", "error_message")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    success: bool
    error_message: str
    def __init__(self, device_id: _Optional[str] = ..., success: bool = ..., error_message: _Optional[str] = ...) -> None: ...

class UpdateRemoteDeviceRequest(_message.Message):
    __slots__ = ("device_id", "name", "url")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    name: str
    url: str
    def __init__(self, device_id: _Optional[str] = ..., name: _Optional[str] = ..., url: _Optional[str] = ...) -> None: ...

class UpdateRemoteDeviceResponse(_message.Message):
    __slots__ = ("success", "error_message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error_message: str
    def __init__(self, success: bool = ..., error_message: _Optional[str] = ...) -> None: ...

class RemoveRemoteDeviceRequest(_message.Message):
    __slots__ = ("device_id",)
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    def __init__(self, device_id: _Optional[str] = ...) -> None: ...

class RemoveRemoteDeviceResponse(_message.Message):
    __slots__ = ("success", "error_message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error_message: str
    def __init__(self, success: bool = ..., error_message: _Optional[str] = ...) -> None: ...
