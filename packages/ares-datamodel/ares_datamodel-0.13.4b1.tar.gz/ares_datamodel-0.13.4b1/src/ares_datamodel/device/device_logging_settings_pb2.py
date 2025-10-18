"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'device/device_logging_settings.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n$device/device_logging_settings.proto\x12\x15ares.datamodel.device"\xbe\x02\n\x15DeviceLoggingSettings\x12\x11\n\tdevice_id\x18\x01 \x01(\t\x12N\n\x0clogging_type\x18\x02 \x01(\x0e28.ares.datamodel.device.DeviceLoggingSettings.LoggingType\x12\x13\n\x0binterval_ms\x18\x03 \x01(\x12\x12H\n\x06deltas\x18\x04 \x03(\x0b28.ares.datamodel.device.DeviceLoggingSettings.DeltasEntry\x1a-\n\x0bDeltasEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x01:\x028\x01"4\n\x0bLoggingType\x12\x08\n\x04NONE\x10\x00\x12\x0c\n\x08INTERVAL\x10\x01\x12\r\n\tON_CHANGE\x10\x02b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'device.device_logging_settings_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_DEVICELOGGINGSETTINGS_DELTASENTRY']._loaded_options = None
    _globals['_DEVICELOGGINGSETTINGS_DELTASENTRY']._serialized_options = b'8\x01'
    _globals['_DEVICELOGGINGSETTINGS']._serialized_start = 64
    _globals['_DEVICELOGGINGSETTINGS']._serialized_end = 382
    _globals['_DEVICELOGGINGSETTINGS_DELTASENTRY']._serialized_start = 283
    _globals['_DEVICELOGGINGSETTINGS_DELTASENTRY']._serialized_end = 328
    _globals['_DEVICELOGGINGSETTINGS_LOGGINGTYPE']._serialized_start = 330
    _globals['_DEVICELOGGINGSETTINGS_LOGGINGTYPE']._serialized_end = 382