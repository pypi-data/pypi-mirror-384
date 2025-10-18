"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'device/device_polling_settings.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n$device/device_polling_settings.proto\x12\x15ares.datamodel.device"y\n\x15DevicePollingSettings\x12\x11\n\tdevice_id\x18\x01 \x01(\t\x128\n\x0cpolling_type\x18\x02 \x01(\x0e2".ares.datamodel.device.PollingType\x12\x13\n\x0binterval_ms\x18\x03 \x01(\x12*4\n\x0bPollingType\x12\x08\n\x04NONE\x10\x00\x12\x0c\n\x08INTERVAL\x10\x01\x12\r\n\tON_CHANGE\x10\x02b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'device.device_polling_settings_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_POLLINGTYPE']._serialized_start = 186
    _globals['_POLLINGTYPE']._serialized_end = 238
    _globals['_DEVICEPOLLINGSETTINGS']._serialized_start = 63
    _globals['_DEVICEPOLLINGSETTINGS']._serialized_end = 184