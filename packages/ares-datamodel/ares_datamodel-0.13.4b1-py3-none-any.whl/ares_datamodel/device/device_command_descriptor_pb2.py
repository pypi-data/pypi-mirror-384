"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'device/device_command_descriptor.proto')
_sym_db = _symbol_database.Default()
from .. import ares_data_schema_pb2 as ares__data__schema__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n&device/device_command_descriptor.proto\x12\x15ares.datamodel.device\x1a\x16ares_data_schema.proto"\xa9\x01\n\x17DeviceCommandDescriptor\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x13\n\x0bdescription\x18\x02 \x01(\t\x124\n\x0cinput_schema\x18\x05 \x01(\x0b2\x1e.ares.datamodel.AresDataSchema\x125\n\routput_schema\x18\x04 \x01(\x0b2\x1e.ares.datamodel.AresDataSchemab\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'device.device_command_descriptor_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_DEVICECOMMANDDESCRIPTOR']._serialized_start = 90
    _globals['_DEVICECOMMANDDESCRIPTOR']._serialized_end = 259