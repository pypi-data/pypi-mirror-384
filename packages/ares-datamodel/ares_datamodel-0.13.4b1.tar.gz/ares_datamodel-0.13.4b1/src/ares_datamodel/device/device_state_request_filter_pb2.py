"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'device/device_state_request_filter.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from google.protobuf import duration_pb2 as google_dot_protobuf_dot_duration__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n(device/device_state_request_filter.proto\x12\x15ares.datamodel.device\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x1egoogle/protobuf/duration.proto"\xab\x02\n\x18DeviceStateRequestFilter\x12)\n\x05start\x18\x01 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12\'\n\x03end\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12=\n\x17completed_experiment_id\x18\x03 \x01(\x0b2\x1c.google.protobuf.StringValue\x12;\n\x15completed_campaign_id\x18\x04 \x01(\x0b2\x1c.google.protobuf.StringValue\x12+\n\x08interval\x18\x05 \x01(\x0b2\x19.google.protobuf.Duration\x12\x12\n\ndevice_ids\x18\x06 \x03(\tb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'device.device_state_request_filter_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_DEVICESTATEREQUESTFILTER']._serialized_start = 165
    _globals['_DEVICESTATEREQUESTFILTER']._serialized_end = 464