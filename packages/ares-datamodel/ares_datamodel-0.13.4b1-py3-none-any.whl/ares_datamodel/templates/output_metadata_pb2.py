"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'templates/output_metadata.proto')
_sym_db = _symbol_database.Default()
from .. import ares_data_schema_pb2 as ares__data__schema__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1ftemplates/output_metadata.proto\x12\x18ares.datamodel.templates\x1a\x16ares_data_schema.proto"\x8f\x01\n\x0eOutputMetadata\x12\x16\n\tunique_id\x18\x01 \x01(\tH\x00\x88\x01\x01\x123\n\x0bdata_schema\x18\x02 \x01(\x0b2\x1e.ares.datamodel.AresDataSchema\x12\x13\n\x0bdescription\x18\x03 \x01(\t\x12\r\n\x05index\x18\x04 \x01(\x03B\x0c\n\n_unique_idb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'templates.output_metadata_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_OUTPUTMETADATA']._serialized_start = 86
    _globals['_OUTPUTMETADATA']._serialized_end = 229