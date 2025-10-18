"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from . import device_state_export_service_pb2 as device__state__export__service__pb2
GRPC_GENERATED_VERSION = '1.75.1'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + f' but the generated code in device_state_export_service_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class DeviceStateExportServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetStateExport = channel.unary_unary('/ares.services.DeviceStateExportService/GetStateExport', request_serializer=device__state__export__service__pb2.DeviceStateRequest.SerializeToString, response_deserializer=device__state__export__service__pb2.DeviceStateResponse.FromString, _registered_method=True)

class DeviceStateExportServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetStateExport(self, request, context):
        """This returns a byte array that is ready to be saved as a specified format
        ex.: This could return a byte string that represents a zip file
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_DeviceStateExportServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'GetStateExport': grpc.unary_unary_rpc_method_handler(servicer.GetStateExport, request_deserializer=device__state__export__service__pb2.DeviceStateRequest.FromString, response_serializer=device__state__export__service__pb2.DeviceStateResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('ares.services.DeviceStateExportService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('ares.services.DeviceStateExportService', rpc_method_handlers)

class DeviceStateExportService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetStateExport(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.DeviceStateExportService/GetStateExport', device__state__export__service__pb2.DeviceStateRequest.SerializeToString, device__state__export__service__pb2.DeviceStateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)