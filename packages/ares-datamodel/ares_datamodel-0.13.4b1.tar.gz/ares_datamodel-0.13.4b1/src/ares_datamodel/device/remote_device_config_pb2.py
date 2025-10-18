"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'device/remote_device_config.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!device/remote_device_config.proto\x12\x15ares.datamodel.device"U\n\x12RemoteDeviceConfig\x12\x16\n\tunique_id\x18\x01 \x01(\tH\x00\x88\x01\x01\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0b\n\x03url\x18\x03 \x01(\tB\x0c\n\n_unique_idb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'device.remote_device_config_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_REMOTEDEVICECONFIG']._serialized_start = 60
    _globals['_REMOTEDEVICECONFIG']._serialized_end = 145