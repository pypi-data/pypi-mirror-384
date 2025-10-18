"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'device_state_export_service.proto')
_sym_db = _symbol_database.Default()
from .device import device_state_request_filter_pb2 as device_dot_device__state__request__filter__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!device_state_export_service.proto\x12\rares.services\x1a(device/device_state_request_filter.proto"\x85\x01\n\x12DeviceStateRequest\x12?\n\x06filter\x18\x01 \x01(\x0b2/.ares.datamodel.device.DeviceStateRequestFilter\x12.\n\x0bexport_type\x18\x02 \x01(\x0e2\x19.ares.services.ExportType"#\n\x13DeviceStateResponse\x12\x0c\n\x04data\x18\x01 \x01(\x0c*7\n\nExportType\x12\x0f\n\x0bUNSPECIFIED\x10\x00\x12\x0c\n\x08COMBINED\x10\x01\x12\n\n\x06ZIPPED\x10\x022s\n\x18DeviceStateExportService\x12W\n\x0eGetStateExport\x12!.ares.services.DeviceStateRequest\x1a".ares.services.DeviceStateResponseb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'device_state_export_service_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_EXPORTTYPE']._serialized_start = 267
    _globals['_EXPORTTYPE']._serialized_end = 322
    _globals['_DEVICESTATEREQUEST']._serialized_start = 95
    _globals['_DEVICESTATEREQUEST']._serialized_end = 228
    _globals['_DEVICESTATERESPONSE']._serialized_start = 230
    _globals['_DEVICESTATERESPONSE']._serialized_end = 265
    _globals['_DEVICESTATEEXPORTSERVICE']._serialized_start = 324
    _globals['_DEVICESTATEEXPORTSERVICE']._serialized_end = 439