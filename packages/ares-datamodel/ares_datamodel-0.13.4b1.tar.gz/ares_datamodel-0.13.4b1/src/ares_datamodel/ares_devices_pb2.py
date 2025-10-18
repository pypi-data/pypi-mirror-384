"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'ares_devices.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from .templates import command_metadata_pb2 as templates_dot_command__metadata__pb2
from .templates import command_template_pb2 as templates_dot_command__template__pb2
from .device import device_execution_result_pb2 as device_dot_device__execution__result__pb2
from .device import remote_device_config_pb2 as device_dot_remote__device__config__pb2
from .device import device_status_pb2 as device_dot_device__status__pb2
from .device import device_info_pb2 as device_dot_device__info__pb2
from .device import device_config_pb2 as device_dot_device__config__pb2
from .device import device_settings_pb2 as device_dot_device__settings__pb2
from .device import device_polling_settings_pb2 as device_dot_device__polling__settings__pb2
from . import ares_struct_pb2 as ares__struct__pb2
from . import ares_data_schema_pb2 as ares__data__schema__pb2
from .device import device_logging_settings_pb2 as device_dot_device__logging__settings__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x12ares_devices.proto\x12\x14ares.services.device\x1a\x1bgoogle/protobuf/empty.proto\x1a templates/command_metadata.proto\x1a templates/command_template.proto\x1a$device/device_execution_result.proto\x1a!device/remote_device_config.proto\x1a\x1adevice/device_status.proto\x1a\x18device/device_info.proto\x1a\x1adevice/device_config.proto\x1a\x1cdevice/device_settings.proto\x1a$device/device_polling_settings.proto\x1a\x11ares_struct.proto\x1a\x16ares_data_schema.proto\x1a$device/device_logging_settings.proto"R\n\x17ListAresDevicesResponse\x127\n\x0cares_devices\x18\x01 \x03(\x0b2!.ares.datamodel.device.DeviceInfo"S\n\x1dListAresRemoteDevicesResponse\x122\n\x07devices\x18\x01 \x03(\x0b2!.ares.datamodel.device.DeviceInfo"5\n\x1dListServerSerialPortsResponse\x12\x14\n\x0cserial_ports\x18\x01 \x03(\t",\n\x17CommandMetadatasRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t"X\n\x18CommandMetadatasResponse\x12<\n\tmetadatas\x18\x01 \x03(\x0b2).ares.datamodel.templates.CommandMetadata"(\n\x13DeviceStatusRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t"u\n\x18DeviceStateStreamRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t\x12F\n\x10polling_settings\x18\x02 \x01(\x0b2,.ares.datamodel.device.DevicePollingSettings"\'\n\x12DeviceStateRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t"@\n\x13DeviceStateResponse\x12)\n\x05state\x18\x01 \x01(\x0b2\x1a.ares.datamodel.AresStruct"-\n\x18DeviceStateSchemaRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t"K\n\x19DeviceStateSchemaResponse\x12.\n\x06schema\x18\x01 \x01(\x0b2\x1e.ares.datamodel.AresDataSchema"0\n\x1bDeviceLoggerSettingsRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t"V\n\x15DeviceLoggersResponse\x12=\n\x07loggers\x18\x01 \x03(\x0b2,.ares.datamodel.device.DeviceLoggingSettings"&\n\x11DeviceInfoRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t"*\n\x15DeviceSettingsRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t"*\n\x15DeviceActivateRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t"*\n\x13DeviceConfigRequest\x12\x13\n\x0bdevice_type\x18\x01 \x01(\t"L\n\x14DeviceConfigResponse\x124\n\x07configs\x18\x01 \x03(\x0b2#.ares.datamodel.device.DeviceConfig"X\n\x1aRemoteDeviceConfigResponse\x12:\n\x07configs\x18\x01 \x03(\x0b2).ares.datamodel.device.RemoteDeviceConfig"3\n\x16AddRemoteDeviceRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0b\n\x03url\x18\x02 \x01(\t"k\n\x17AddRemoteDeviceResponse\x12\x11\n\tdevice_id\x18\x01 \x01(\t\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x1a\n\rerror_message\x18\x03 \x01(\tH\x00\x88\x01\x01B\x10\n\x0e_error_message"d\n\x19UpdateRemoteDeviceRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t\x12\x11\n\x04name\x18\x02 \x01(\tH\x00\x88\x01\x01\x12\x10\n\x03url\x18\x03 \x01(\tH\x01\x88\x01\x01B\x07\n\x05_nameB\x06\n\x04_url"[\n\x1aUpdateRemoteDeviceResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x1a\n\rerror_message\x18\x02 \x01(\tH\x00\x88\x01\x01B\x10\n\x0e_error_message".\n\x19RemoveRemoteDeviceRequest\x12\x11\n\tdevice_id\x18\x01 \x01(\t"[\n\x1aRemoveRemoteDeviceResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x1a\n\rerror_message\x18\x02 \x01(\tH\x00\x88\x01\x01B\x10\n\x0e_error_message2\xa4\x11\n\x0bAresDevices\x12X\n\x0fListAresDevices\x12\x16.google.protobuf.Empty\x1a-.ares.services.device.ListAresDevicesResponse\x12[\n\rGetDeviceInfo\x12\'.ares.services.device.DeviceInfoRequest\x1a!.ares.datamodel.device.DeviceInfo\x12c\n\x14GetServerSerialPorts\x12\x16.google.protobuf.Empty\x1a3.ares.services.device.ListServerSerialPortsResponse\x12l\n\x0fGetDeviceStatus\x12).ares.services.device.DeviceStatusRequest\x1a..ares.datamodel.device.DeviceOperationalStatus\x12t\n\x13GetCommandMetadatas\x12-.ares.services.device.CommandMetadatasRequest\x1a..ares.services.device.CommandMetadatasResponse\x12i\n\x0eExecuteCommand\x12).ares.datamodel.templates.CommandTemplate\x1a,.ares.datamodel.device.DeviceExecutionResult\x12l\n\x13GetAllDeviceConfigs\x12).ares.services.device.DeviceConfigRequest\x1a*.ares.services.device.DeviceConfigResponse\x12O\n\x08Activate\x12+.ares.services.device.DeviceActivateRequest\x1a\x16.google.protobuf.Empty\x12R\n\x11SetDeviceSettings\x12%.ares.datamodel.device.DeviceSettings\x1a\x16.google.protobuf.Empty\x12\\\n\x11GetDeviceSettings\x12+.ares.services.device.DeviceSettingsRequest\x1a\x1a.ares.datamodel.AresStruct\x12e\n\x0eGetDeviceState\x12(.ares.services.device.DeviceStateRequest\x1a).ares.services.device.DeviceStateResponse\x12s\n\x14GetDeviceStateStream\x12..ares.services.device.DeviceStateStreamRequest\x1a).ares.services.device.DeviceStateResponse0\x01\x12w\n\x14GetDeviceStateSchema\x12..ares.services.device.DeviceStateSchemaRequest\x1a/.ares.services.device.DeviceStateSchemaResponse\x12_\n\x17SetDeviceLoggerSettings\x12,.ares.datamodel.device.DeviceLoggingSettings\x1a\x16.google.protobuf.Empty\x12z\n\x17GetDeviceLoggerSettings\x121.ares.services.device.DeviceLoggerSettingsRequest\x1a,.ares.datamodel.device.DeviceLoggingSettings\x12W\n\x10GetDeviceLoggers\x12\x16.google.protobuf.Empty\x1a+.ares.services.device.DeviceLoggersResponse\x12d\n\x15ListRemoteAresDevices\x12\x16.google.protobuf.Empty\x1a3.ares.services.device.ListAresRemoteDevicesResponse\x12n\n\x0fAddRemoteDevice\x12,.ares.services.device.AddRemoteDeviceRequest\x1a-.ares.services.device.AddRemoteDeviceResponse\x12w\n\x12RemoveRemoteDevice\x12/.ares.services.device.RemoveRemoteDeviceRequest\x1a0.ares.services.device.RemoveRemoteDeviceResponse\x12w\n\x12UpdateRemoteDevice\x12/.ares.services.device.UpdateRemoteDeviceRequest\x1a0.ares.services.device.UpdateRemoteDeviceResponse\x12f\n\x1aGetAllRemoteDevicesConfigs\x12\x16.google.protobuf.Empty\x1a0.ares.services.device.RemoteDeviceConfigResponseb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ares_devices_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_LISTARESDEVICESRESPONSE']._serialized_start = 445
    _globals['_LISTARESDEVICESRESPONSE']._serialized_end = 527
    _globals['_LISTARESREMOTEDEVICESRESPONSE']._serialized_start = 529
    _globals['_LISTARESREMOTEDEVICESRESPONSE']._serialized_end = 612
    _globals['_LISTSERVERSERIALPORTSRESPONSE']._serialized_start = 614
    _globals['_LISTSERVERSERIALPORTSRESPONSE']._serialized_end = 667
    _globals['_COMMANDMETADATASREQUEST']._serialized_start = 669
    _globals['_COMMANDMETADATASREQUEST']._serialized_end = 713
    _globals['_COMMANDMETADATASRESPONSE']._serialized_start = 715
    _globals['_COMMANDMETADATASRESPONSE']._serialized_end = 803
    _globals['_DEVICESTATUSREQUEST']._serialized_start = 805
    _globals['_DEVICESTATUSREQUEST']._serialized_end = 845
    _globals['_DEVICESTATESTREAMREQUEST']._serialized_start = 847
    _globals['_DEVICESTATESTREAMREQUEST']._serialized_end = 964
    _globals['_DEVICESTATEREQUEST']._serialized_start = 966
    _globals['_DEVICESTATEREQUEST']._serialized_end = 1005
    _globals['_DEVICESTATERESPONSE']._serialized_start = 1007
    _globals['_DEVICESTATERESPONSE']._serialized_end = 1071
    _globals['_DEVICESTATESCHEMAREQUEST']._serialized_start = 1073
    _globals['_DEVICESTATESCHEMAREQUEST']._serialized_end = 1118
    _globals['_DEVICESTATESCHEMARESPONSE']._serialized_start = 1120
    _globals['_DEVICESTATESCHEMARESPONSE']._serialized_end = 1195
    _globals['_DEVICELOGGERSETTINGSREQUEST']._serialized_start = 1197
    _globals['_DEVICELOGGERSETTINGSREQUEST']._serialized_end = 1245
    _globals['_DEVICELOGGERSRESPONSE']._serialized_start = 1247
    _globals['_DEVICELOGGERSRESPONSE']._serialized_end = 1333
    _globals['_DEVICEINFOREQUEST']._serialized_start = 1335
    _globals['_DEVICEINFOREQUEST']._serialized_end = 1373
    _globals['_DEVICESETTINGSREQUEST']._serialized_start = 1375
    _globals['_DEVICESETTINGSREQUEST']._serialized_end = 1417
    _globals['_DEVICEACTIVATEREQUEST']._serialized_start = 1419
    _globals['_DEVICEACTIVATEREQUEST']._serialized_end = 1461
    _globals['_DEVICECONFIGREQUEST']._serialized_start = 1463
    _globals['_DEVICECONFIGREQUEST']._serialized_end = 1505
    _globals['_DEVICECONFIGRESPONSE']._serialized_start = 1507
    _globals['_DEVICECONFIGRESPONSE']._serialized_end = 1583
    _globals['_REMOTEDEVICECONFIGRESPONSE']._serialized_start = 1585
    _globals['_REMOTEDEVICECONFIGRESPONSE']._serialized_end = 1673
    _globals['_ADDREMOTEDEVICEREQUEST']._serialized_start = 1675
    _globals['_ADDREMOTEDEVICEREQUEST']._serialized_end = 1726
    _globals['_ADDREMOTEDEVICERESPONSE']._serialized_start = 1728
    _globals['_ADDREMOTEDEVICERESPONSE']._serialized_end = 1835
    _globals['_UPDATEREMOTEDEVICEREQUEST']._serialized_start = 1837
    _globals['_UPDATEREMOTEDEVICEREQUEST']._serialized_end = 1937
    _globals['_UPDATEREMOTEDEVICERESPONSE']._serialized_start = 1939
    _globals['_UPDATEREMOTEDEVICERESPONSE']._serialized_end = 2030
    _globals['_REMOVEREMOTEDEVICEREQUEST']._serialized_start = 2032
    _globals['_REMOVEREMOTEDEVICEREQUEST']._serialized_end = 2078
    _globals['_REMOVEREMOTEDEVICERESPONSE']._serialized_start = 2080
    _globals['_REMOVEREMOTEDEVICERESPONSE']._serialized_end = 2171
    _globals['_ARESDEVICES']._serialized_start = 2174
    _globals['_ARESDEVICES']._serialized_end = 4386