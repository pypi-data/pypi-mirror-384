"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'device/device_execution_result.proto')
_sym_db = _symbol_database.Default()
from .. import ares_struct_pb2 as ares__struct__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n$device/device_execution_result.proto\x12\x15ares.datamodel.device\x1a\x11ares_struct.proto"c\n\x15DeviceExecutionResult\x12*\n\x06result\x18\x01 \x01(\x0b2\x1a.ares.datamodel.AresStruct\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\r\n\x05error\x18\x03 \x01(\tb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'device.device_execution_result_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_DEVICEEXECUTIONRESULT']._serialized_start = 82
    _globals['_DEVICEEXECUTIONRESULT']._serialized_end = 181