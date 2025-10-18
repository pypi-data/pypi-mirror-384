"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from ...device import device_execution_result_pb2 as device_dot_device__execution__result__pb2
from ...device import device_status_pb2 as device_dot_device__status__pb2
from ...device.remote import ares_remote_device_service_pb2 as device_dot_remote_dot_ares__remote__device__service__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
GRPC_GENERATED_VERSION = '1.75.1'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + f' but the generated code in device/remote/ares_remote_device_service_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class AresRemoteDeviceServiceStub(object):
    """defines a contract for ares to use in order to talk to a remote device
    designed to be similar to the internal ARES device implementation
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetOperationalStatus = channel.unary_unary('/ares.datamodel.device.remote.AresRemoteDeviceService/GetOperationalStatus', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=device_dot_device__status__pb2.DeviceOperationalStatus.FromString, _registered_method=True)
        self.GetInfo = channel.unary_unary('/ares.datamodel.device.remote.AresRemoteDeviceService/GetInfo', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=device_dot_remote_dot_ares__remote__device__service__pb2.DeviceInfoResponse.FromString, _registered_method=True)
        self.GetCommands = channel.unary_unary('/ares.datamodel.device.remote.AresRemoteDeviceService/GetCommands', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=device_dot_remote_dot_ares__remote__device__service__pb2.CommandsResponse.FromString, _registered_method=True)
        self.ExecuteCommand = channel.unary_unary('/ares.datamodel.device.remote.AresRemoteDeviceService/ExecuteCommand', request_serializer=device_dot_remote_dot_ares__remote__device__service__pb2.ExecuteCommandRequest.SerializeToString, response_deserializer=device_dot_device__execution__result__pb2.DeviceExecutionResult.FromString, _registered_method=True)
        self.EnterSafeMode = channel.unary_unary('/ares.datamodel.device.remote.AresRemoteDeviceService/EnterSafeMode', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.GetSettingsSchema = channel.unary_unary('/ares.datamodel.device.remote.AresRemoteDeviceService/GetSettingsSchema', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=device_dot_remote_dot_ares__remote__device__service__pb2.SettingsSchemaResponse.FromString, _registered_method=True)
        self.GetCurrentSettings = channel.unary_unary('/ares.datamodel.device.remote.AresRemoteDeviceService/GetCurrentSettings', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=device_dot_remote_dot_ares__remote__device__service__pb2.CurrentSettingsResponse.FromString, _registered_method=True)
        self.SetSettings = channel.unary_unary('/ares.datamodel.device.remote.AresRemoteDeviceService/SetSettings', request_serializer=device_dot_remote_dot_ares__remote__device__service__pb2.SetSettingsRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.GetStateSchema = channel.unary_unary('/ares.datamodel.device.remote.AresRemoteDeviceService/GetStateSchema', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=device_dot_remote_dot_ares__remote__device__service__pb2.StateSchemaResponse.FromString, _registered_method=True)
        self.GetState = channel.unary_unary('/ares.datamodel.device.remote.AresRemoteDeviceService/GetState', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=device_dot_remote_dot_ares__remote__device__service__pb2.DeviceStateResponse.FromString, _registered_method=True)
        self.GetStateStream = channel.unary_stream('/ares.datamodel.device.remote.AresRemoteDeviceService/GetStateStream', request_serializer=device_dot_remote_dot_ares__remote__device__service__pb2.DeviceStateStreamRequest.SerializeToString, response_deserializer=device_dot_remote_dot_ares__remote__device__service__pb2.DeviceStateResponse.FromString, _registered_method=True)

class AresRemoteDeviceServiceServicer(object):
    """defines a contract for ares to use in order to talk to a remote device
    designed to be similar to the internal ARES device implementation
    """

    def GetOperationalStatus(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetCommands(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ExecuteCommand(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def EnterSafeMode(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetSettingsSchema(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetCurrentSettings(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetSettings(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetStateSchema(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetState(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetStateStream(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_AresRemoteDeviceServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'GetOperationalStatus': grpc.unary_unary_rpc_method_handler(servicer.GetOperationalStatus, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=device_dot_device__status__pb2.DeviceOperationalStatus.SerializeToString), 'GetInfo': grpc.unary_unary_rpc_method_handler(servicer.GetInfo, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=device_dot_remote_dot_ares__remote__device__service__pb2.DeviceInfoResponse.SerializeToString), 'GetCommands': grpc.unary_unary_rpc_method_handler(servicer.GetCommands, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=device_dot_remote_dot_ares__remote__device__service__pb2.CommandsResponse.SerializeToString), 'ExecuteCommand': grpc.unary_unary_rpc_method_handler(servicer.ExecuteCommand, request_deserializer=device_dot_remote_dot_ares__remote__device__service__pb2.ExecuteCommandRequest.FromString, response_serializer=device_dot_device__execution__result__pb2.DeviceExecutionResult.SerializeToString), 'EnterSafeMode': grpc.unary_unary_rpc_method_handler(servicer.EnterSafeMode, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'GetSettingsSchema': grpc.unary_unary_rpc_method_handler(servicer.GetSettingsSchema, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=device_dot_remote_dot_ares__remote__device__service__pb2.SettingsSchemaResponse.SerializeToString), 'GetCurrentSettings': grpc.unary_unary_rpc_method_handler(servicer.GetCurrentSettings, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=device_dot_remote_dot_ares__remote__device__service__pb2.CurrentSettingsResponse.SerializeToString), 'SetSettings': grpc.unary_unary_rpc_method_handler(servicer.SetSettings, request_deserializer=device_dot_remote_dot_ares__remote__device__service__pb2.SetSettingsRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'GetStateSchema': grpc.unary_unary_rpc_method_handler(servicer.GetStateSchema, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=device_dot_remote_dot_ares__remote__device__service__pb2.StateSchemaResponse.SerializeToString), 'GetState': grpc.unary_unary_rpc_method_handler(servicer.GetState, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=device_dot_remote_dot_ares__remote__device__service__pb2.DeviceStateResponse.SerializeToString), 'GetStateStream': grpc.unary_stream_rpc_method_handler(servicer.GetStateStream, request_deserializer=device_dot_remote_dot_ares__remote__device__service__pb2.DeviceStateStreamRequest.FromString, response_serializer=device_dot_remote_dot_ares__remote__device__service__pb2.DeviceStateResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('ares.datamodel.device.remote.AresRemoteDeviceService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('ares.datamodel.device.remote.AresRemoteDeviceService', rpc_method_handlers)

class AresRemoteDeviceService(object):
    """defines a contract for ares to use in order to talk to a remote device
    designed to be similar to the internal ARES device implementation
    """

    @staticmethod
    def GetOperationalStatus(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/GetOperationalStatus', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, device_dot_device__status__pb2.DeviceOperationalStatus.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetInfo(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/GetInfo', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, device_dot_remote_dot_ares__remote__device__service__pb2.DeviceInfoResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetCommands(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/GetCommands', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, device_dot_remote_dot_ares__remote__device__service__pb2.CommandsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ExecuteCommand(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/ExecuteCommand', device_dot_remote_dot_ares__remote__device__service__pb2.ExecuteCommandRequest.SerializeToString, device_dot_device__execution__result__pb2.DeviceExecutionResult.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def EnterSafeMode(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/EnterSafeMode', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetSettingsSchema(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/GetSettingsSchema', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, device_dot_remote_dot_ares__remote__device__service__pb2.SettingsSchemaResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetCurrentSettings(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/GetCurrentSettings', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, device_dot_remote_dot_ares__remote__device__service__pb2.CurrentSettingsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def SetSettings(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/SetSettings', device_dot_remote_dot_ares__remote__device__service__pb2.SetSettingsRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetStateSchema(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/GetStateSchema', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, device_dot_remote_dot_ares__remote__device__service__pb2.StateSchemaResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetState(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/GetState', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, device_dot_remote_dot_ares__remote__device__service__pb2.DeviceStateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetStateStream(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_stream(request, target, '/ares.datamodel.device.remote.AresRemoteDeviceService/GetStateStream', device_dot_remote_dot_ares__remote__device__service__pb2.DeviceStateStreamRequest.SerializeToString, device_dot_remote_dot_ares__remote__device__service__pb2.DeviceStateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)