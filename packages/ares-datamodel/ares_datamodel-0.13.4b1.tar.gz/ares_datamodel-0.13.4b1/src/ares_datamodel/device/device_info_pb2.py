"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'device/device_info.proto')
_sym_db = _symbol_database.Default()
from .. import ares_data_schema_pb2 as ares__data__schema__pb2
from ..device import device_command_descriptor_pb2 as device_dot_device__command__descriptor__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x18device/device_info.proto\x12\x15ares.datamodel.device\x1a\x16ares_data_schema.proto\x1a&device/device_command_descriptor.proto"\xa4\x02\n\nDeviceInfo\x12\x11\n\tunique_id\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0c\n\x04type\x18\x03 \x01(\t\x12\x18\n\x0bdescription\x18\x04 \x01(\tH\x00\x88\x01\x01\x12\x0f\n\x07version\x18\x05 \x01(\t\x12\x10\n\x03url\x18\x06 \x01(\tH\x01\x88\x01\x01\x12<\n\x0fsettings_schema\x18\x07 \x01(\x0b2\x1e.ares.datamodel.AresDataSchemaH\x02\x88\x01\x01\x12@\n\x08commands\x18\x08 \x03(\x0b2..ares.datamodel.device.DeviceCommandDescriptorB\x0e\n\x0c_descriptionB\x06\n\x04_urlB\x12\n\x10_settings_schemab\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'device.device_info_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_DEVICEINFO']._serialized_start = 116
    _globals['_DEVICEINFO']._serialized_end = 408