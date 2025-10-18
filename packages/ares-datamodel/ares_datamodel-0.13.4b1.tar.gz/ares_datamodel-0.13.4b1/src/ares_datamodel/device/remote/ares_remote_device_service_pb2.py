"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'device/remote/ares_remote_device_service.proto')
_sym_db = _symbol_database.Default()
from ... import ares_struct_pb2 as ares__struct__pb2
from ...device import device_status_pb2 as device_dot_device__status__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from ... import ares_data_schema_pb2 as ares__data__schema__pb2
from ...device import device_command_descriptor_pb2 as device_dot_device__command__descriptor__pb2
from ...device import device_execution_result_pb2 as device_dot_device__execution__result__pb2
from ...device import device_polling_settings_pb2 as device_dot_device__polling__settings__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n.device/remote/ares_remote_device_service.proto\x12\x1cares.datamodel.device.remote\x1a\x11ares_struct.proto\x1a\x1adevice/device_status.proto\x1a\x1bgoogle/protobuf/empty.proto\x1a\x16ares_data_schema.proto\x1a&device/device_command_descriptor.proto\x1a$device/device_execution_result.proto\x1a$device/device_polling_settings.proto"]\n\x12DeviceInfoResponse\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07version\x18\x02 \x01(\t\x12\x18\n\x0bdescription\x18\x03 \x01(\tH\x00\x88\x01\x01B\x0e\n\x0c_description"H\n\x16SettingsSchemaResponse\x12.\n\x06schema\x18\x01 \x01(\x0b2\x1e.ares.datamodel.AresDataSchema"G\n\x17CurrentSettingsResponse\x12,\n\x08settings\x18\x01 \x01(\x0b2\x1a.ares.datamodel.AresStruct"B\n\x12SetSettingsRequest\x12,\n\x08settings\x18\x01 \x01(\x0b2\x1a.ares.datamodel.AresStruct"T\n\x10CommandsResponse\x12@\n\x08commands\x18\x01 \x03(\x0b2..ares.datamodel.device.DeviceCommandDescriptor"b\n\x18DeviceStateStreamRequest\x12F\n\x10polling_settings\x18\x01 \x01(\x0b2,.ares.datamodel.device.DevicePollingSettings"E\n\x13StateSchemaResponse\x12.\n\x06schema\x18\x01 \x01(\x0b2\x1e.ares.datamodel.AresDataSchema"@\n\x13DeviceStateResponse\x12)\n\x05state\x18\x01 \x01(\x0b2\x1a.ares.datamodel.AresStruct"\\\n\x15ExecuteCommandRequest\x12\x14\n\x0ccommand_name\x18\x01 \x01(\t\x12-\n\targuments\x18\x02 \x01(\x0b2\x1a.ares.datamodel.AresStruct2\xaf\x08\n\x17AresRemoteDeviceService\x12^\n\x14GetOperationalStatus\x12\x16.google.protobuf.Empty\x1a..ares.datamodel.device.DeviceOperationalStatus\x12S\n\x07GetInfo\x12\x16.google.protobuf.Empty\x1a0.ares.datamodel.device.remote.DeviceInfoResponse\x12U\n\x0bGetCommands\x12\x16.google.protobuf.Empty\x1a..ares.datamodel.device.remote.CommandsResponse\x12s\n\x0eExecuteCommand\x123.ares.datamodel.device.remote.ExecuteCommandRequest\x1a,.ares.datamodel.device.DeviceExecutionResult\x12?\n\rEnterSafeMode\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\x12a\n\x11GetSettingsSchema\x12\x16.google.protobuf.Empty\x1a4.ares.datamodel.device.remote.SettingsSchemaResponse\x12c\n\x12GetCurrentSettings\x12\x16.google.protobuf.Empty\x1a5.ares.datamodel.device.remote.CurrentSettingsResponse\x12W\n\x0bSetSettings\x120.ares.datamodel.device.remote.SetSettingsRequest\x1a\x16.google.protobuf.Empty\x12[\n\x0eGetStateSchema\x12\x16.google.protobuf.Empty\x1a1.ares.datamodel.device.remote.StateSchemaResponse\x12U\n\x08GetState\x12\x16.google.protobuf.Empty\x1a1.ares.datamodel.device.remote.DeviceStateResponse\x12}\n\x0eGetStateStream\x126.ares.datamodel.device.remote.DeviceStateStreamRequest\x1a1.ares.datamodel.device.remote.DeviceStateResponse0\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'device.remote.ares_remote_device_service_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_DEVICEINFORESPONSE']._serialized_start = 296
    _globals['_DEVICEINFORESPONSE']._serialized_end = 389
    _globals['_SETTINGSSCHEMARESPONSE']._serialized_start = 391
    _globals['_SETTINGSSCHEMARESPONSE']._serialized_end = 463
    _globals['_CURRENTSETTINGSRESPONSE']._serialized_start = 465
    _globals['_CURRENTSETTINGSRESPONSE']._serialized_end = 536
    _globals['_SETSETTINGSREQUEST']._serialized_start = 538
    _globals['_SETSETTINGSREQUEST']._serialized_end = 604
    _globals['_COMMANDSRESPONSE']._serialized_start = 606
    _globals['_COMMANDSRESPONSE']._serialized_end = 690
    _globals['_DEVICESTATESTREAMREQUEST']._serialized_start = 692
    _globals['_DEVICESTATESTREAMREQUEST']._serialized_end = 790
    _globals['_STATESCHEMARESPONSE']._serialized_start = 792
    _globals['_STATESCHEMARESPONSE']._serialized_end = 861
    _globals['_DEVICESTATERESPONSE']._serialized_start = 863
    _globals['_DEVICESTATERESPONSE']._serialized_end = 927
    _globals['_EXECUTECOMMANDREQUEST']._serialized_start = 929
    _globals['_EXECUTECOMMANDREQUEST']._serialized_end = 1021
    _globals['_ARESREMOTEDEVICESERVICE']._serialized_start = 1024
    _globals['_ARESREMOTEDEVICESERVICE']._serialized_end = 2095