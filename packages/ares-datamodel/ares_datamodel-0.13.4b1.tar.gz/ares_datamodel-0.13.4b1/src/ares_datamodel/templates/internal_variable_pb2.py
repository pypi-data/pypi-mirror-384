"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'templates/internal_variable.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!templates/internal_variable.proto\x12\x18ares.datamodel.templates"\xa1\x01\n\x1aInternalVariableAllocation\x12\x16\n\tunique_id\x18\x01 \x01(\tH\x00\x88\x01\x01\x12N\n\x16internal_variable_type\x18\x02 \x01(\x0e2..ares.datamodel.templates.InternalVariableType\x12\r\n\x05value\x18\x03 \x01(\tB\x0c\n\n_unique_id*~\n\x14InternalVariableType\x12\x13\n\x0fVAR_UNSPECIFIED\x10\x00\x12\x1d\n\x19CURRENT_EXPERIMENT_NUMBER\x10\x01\x12\x17\n\x13CURRENT_CAMPAIGN_ID\x10\x02\x12\x19\n\x15CURRENT_CAMPAIGN_NAME\x10\x03b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'templates.internal_variable_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_INTERNALVARIABLETYPE']._serialized_start = 227
    _globals['_INTERNALVARIABLETYPE']._serialized_end = 353
    _globals['_INTERNALVARIABLEALLOCATION']._serialized_start = 64
    _globals['_INTERNALVARIABLEALLOCATION']._serialized_end = 225