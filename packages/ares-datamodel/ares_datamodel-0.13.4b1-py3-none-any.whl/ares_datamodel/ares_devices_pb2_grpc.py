"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from . import ares_devices_pb2 as ares__devices__pb2
from . import ares_struct_pb2 as ares__struct__pb2
from .device import device_execution_result_pb2 as device_dot_device__execution__result__pb2
from .device import device_info_pb2 as device_dot_device__info__pb2
from .device import device_logging_settings_pb2 as device_dot_device__logging__settings__pb2
from .device import device_settings_pb2 as device_dot_device__settings__pb2
from .device import device_status_pb2 as device_dot_device__status__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from .templates import command_template_pb2 as templates_dot_command__template__pb2
GRPC_GENERATED_VERSION = '1.75.1'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + f' but the generated code in ares_devices_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class AresDevicesStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ListAresDevices = channel.unary_unary('/ares.services.device.AresDevices/ListAresDevices', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=ares__devices__pb2.ListAresDevicesResponse.FromString, _registered_method=True)
        self.GetDeviceInfo = channel.unary_unary('/ares.services.device.AresDevices/GetDeviceInfo', request_serializer=ares__devices__pb2.DeviceInfoRequest.SerializeToString, response_deserializer=device_dot_device__info__pb2.DeviceInfo.FromString, _registered_method=True)
        self.GetServerSerialPorts = channel.unary_unary('/ares.services.device.AresDevices/GetServerSerialPorts', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=ares__devices__pb2.ListServerSerialPortsResponse.FromString, _registered_method=True)
        self.GetDeviceStatus = channel.unary_unary('/ares.services.device.AresDevices/GetDeviceStatus', request_serializer=ares__devices__pb2.DeviceStatusRequest.SerializeToString, response_deserializer=device_dot_device__status__pb2.DeviceOperationalStatus.FromString, _registered_method=True)
        self.GetCommandMetadatas = channel.unary_unary('/ares.services.device.AresDevices/GetCommandMetadatas', request_serializer=ares__devices__pb2.CommandMetadatasRequest.SerializeToString, response_deserializer=ares__devices__pb2.CommandMetadatasResponse.FromString, _registered_method=True)
        self.ExecuteCommand = channel.unary_unary('/ares.services.device.AresDevices/ExecuteCommand', request_serializer=templates_dot_command__template__pb2.CommandTemplate.SerializeToString, response_deserializer=device_dot_device__execution__result__pb2.DeviceExecutionResult.FromString, _registered_method=True)
        self.GetAllDeviceConfigs = channel.unary_unary('/ares.services.device.AresDevices/GetAllDeviceConfigs', request_serializer=ares__devices__pb2.DeviceConfigRequest.SerializeToString, response_deserializer=ares__devices__pb2.DeviceConfigResponse.FromString, _registered_method=True)
        self.Activate = channel.unary_unary('/ares.services.device.AresDevices/Activate', request_serializer=ares__devices__pb2.DeviceActivateRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.SetDeviceSettings = channel.unary_unary('/ares.services.device.AresDevices/SetDeviceSettings', request_serializer=device_dot_device__settings__pb2.DeviceSettings.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.GetDeviceSettings = channel.unary_unary('/ares.services.device.AresDevices/GetDeviceSettings', request_serializer=ares__devices__pb2.DeviceSettingsRequest.SerializeToString, response_deserializer=ares__struct__pb2.AresStruct.FromString, _registered_method=True)
        self.GetDeviceState = channel.unary_unary('/ares.services.device.AresDevices/GetDeviceState', request_serializer=ares__devices__pb2.DeviceStateRequest.SerializeToString, response_deserializer=ares__devices__pb2.DeviceStateResponse.FromString, _registered_method=True)
        self.GetDeviceStateStream = channel.unary_stream('/ares.services.device.AresDevices/GetDeviceStateStream', request_serializer=ares__devices__pb2.DeviceStateStreamRequest.SerializeToString, response_deserializer=ares__devices__pb2.DeviceStateResponse.FromString, _registered_method=True)
        self.GetDeviceStateSchema = channel.unary_unary('/ares.services.device.AresDevices/GetDeviceStateSchema', request_serializer=ares__devices__pb2.DeviceStateSchemaRequest.SerializeToString, response_deserializer=ares__devices__pb2.DeviceStateSchemaResponse.FromString, _registered_method=True)
        self.SetDeviceLoggerSettings = channel.unary_unary('/ares.services.device.AresDevices/SetDeviceLoggerSettings', request_serializer=device_dot_device__logging__settings__pb2.DeviceLoggingSettings.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.GetDeviceLoggerSettings = channel.unary_unary('/ares.services.device.AresDevices/GetDeviceLoggerSettings', request_serializer=ares__devices__pb2.DeviceLoggerSettingsRequest.SerializeToString, response_deserializer=device_dot_device__logging__settings__pb2.DeviceLoggingSettings.FromString, _registered_method=True)
        self.GetDeviceLoggers = channel.unary_unary('/ares.services.device.AresDevices/GetDeviceLoggers', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=ares__devices__pb2.DeviceLoggersResponse.FromString, _registered_method=True)
        self.ListRemoteAresDevices = channel.unary_unary('/ares.services.device.AresDevices/ListRemoteAresDevices', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=ares__devices__pb2.ListAresRemoteDevicesResponse.FromString, _registered_method=True)
        self.AddRemoteDevice = channel.unary_unary('/ares.services.device.AresDevices/AddRemoteDevice', request_serializer=ares__devices__pb2.AddRemoteDeviceRequest.SerializeToString, response_deserializer=ares__devices__pb2.AddRemoteDeviceResponse.FromString, _registered_method=True)
        self.RemoveRemoteDevice = channel.unary_unary('/ares.services.device.AresDevices/RemoveRemoteDevice', request_serializer=ares__devices__pb2.RemoveRemoteDeviceRequest.SerializeToString, response_deserializer=ares__devices__pb2.RemoveRemoteDeviceResponse.FromString, _registered_method=True)
        self.UpdateRemoteDevice = channel.unary_unary('/ares.services.device.AresDevices/UpdateRemoteDevice', request_serializer=ares__devices__pb2.UpdateRemoteDeviceRequest.SerializeToString, response_deserializer=ares__devices__pb2.UpdateRemoteDeviceResponse.FromString, _registered_method=True)
        self.GetAllRemoteDevicesConfigs = channel.unary_unary('/ares.services.device.AresDevices/GetAllRemoteDevicesConfigs', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=ares__devices__pb2.RemoteDeviceConfigResponse.FromString, _registered_method=True)

class AresDevicesServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ListAresDevices(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDeviceInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetServerSerialPorts(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDeviceStatus(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetCommandMetadatas(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ExecuteCommand(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAllDeviceConfigs(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Activate(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetDeviceSettings(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDeviceSettings(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDeviceState(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDeviceStateStream(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDeviceStateSchema(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetDeviceLoggerSettings(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDeviceLoggerSettings(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDeviceLoggers(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ListRemoteAresDevices(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AddRemoteDevice(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RemoveRemoteDevice(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateRemoteDevice(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAllRemoteDevicesConfigs(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_AresDevicesServicer_to_server(servicer, server):
    rpc_method_handlers = {'ListAresDevices': grpc.unary_unary_rpc_method_handler(servicer.ListAresDevices, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=ares__devices__pb2.ListAresDevicesResponse.SerializeToString), 'GetDeviceInfo': grpc.unary_unary_rpc_method_handler(servicer.GetDeviceInfo, request_deserializer=ares__devices__pb2.DeviceInfoRequest.FromString, response_serializer=device_dot_device__info__pb2.DeviceInfo.SerializeToString), 'GetServerSerialPorts': grpc.unary_unary_rpc_method_handler(servicer.GetServerSerialPorts, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=ares__devices__pb2.ListServerSerialPortsResponse.SerializeToString), 'GetDeviceStatus': grpc.unary_unary_rpc_method_handler(servicer.GetDeviceStatus, request_deserializer=ares__devices__pb2.DeviceStatusRequest.FromString, response_serializer=device_dot_device__status__pb2.DeviceOperationalStatus.SerializeToString), 'GetCommandMetadatas': grpc.unary_unary_rpc_method_handler(servicer.GetCommandMetadatas, request_deserializer=ares__devices__pb2.CommandMetadatasRequest.FromString, response_serializer=ares__devices__pb2.CommandMetadatasResponse.SerializeToString), 'ExecuteCommand': grpc.unary_unary_rpc_method_handler(servicer.ExecuteCommand, request_deserializer=templates_dot_command__template__pb2.CommandTemplate.FromString, response_serializer=device_dot_device__execution__result__pb2.DeviceExecutionResult.SerializeToString), 'GetAllDeviceConfigs': grpc.unary_unary_rpc_method_handler(servicer.GetAllDeviceConfigs, request_deserializer=ares__devices__pb2.DeviceConfigRequest.FromString, response_serializer=ares__devices__pb2.DeviceConfigResponse.SerializeToString), 'Activate': grpc.unary_unary_rpc_method_handler(servicer.Activate, request_deserializer=ares__devices__pb2.DeviceActivateRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'SetDeviceSettings': grpc.unary_unary_rpc_method_handler(servicer.SetDeviceSettings, request_deserializer=device_dot_device__settings__pb2.DeviceSettings.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'GetDeviceSettings': grpc.unary_unary_rpc_method_handler(servicer.GetDeviceSettings, request_deserializer=ares__devices__pb2.DeviceSettingsRequest.FromString, response_serializer=ares__struct__pb2.AresStruct.SerializeToString), 'GetDeviceState': grpc.unary_unary_rpc_method_handler(servicer.GetDeviceState, request_deserializer=ares__devices__pb2.DeviceStateRequest.FromString, response_serializer=ares__devices__pb2.DeviceStateResponse.SerializeToString), 'GetDeviceStateStream': grpc.unary_stream_rpc_method_handler(servicer.GetDeviceStateStream, request_deserializer=ares__devices__pb2.DeviceStateStreamRequest.FromString, response_serializer=ares__devices__pb2.DeviceStateResponse.SerializeToString), 'GetDeviceStateSchema': grpc.unary_unary_rpc_method_handler(servicer.GetDeviceStateSchema, request_deserializer=ares__devices__pb2.DeviceStateSchemaRequest.FromString, response_serializer=ares__devices__pb2.DeviceStateSchemaResponse.SerializeToString), 'SetDeviceLoggerSettings': grpc.unary_unary_rpc_method_handler(servicer.SetDeviceLoggerSettings, request_deserializer=device_dot_device__logging__settings__pb2.DeviceLoggingSettings.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'GetDeviceLoggerSettings': grpc.unary_unary_rpc_method_handler(servicer.GetDeviceLoggerSettings, request_deserializer=ares__devices__pb2.DeviceLoggerSettingsRequest.FromString, response_serializer=device_dot_device__logging__settings__pb2.DeviceLoggingSettings.SerializeToString), 'GetDeviceLoggers': grpc.unary_unary_rpc_method_handler(servicer.GetDeviceLoggers, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=ares__devices__pb2.DeviceLoggersResponse.SerializeToString), 'ListRemoteAresDevices': grpc.unary_unary_rpc_method_handler(servicer.ListRemoteAresDevices, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=ares__devices__pb2.ListAresRemoteDevicesResponse.SerializeToString), 'AddRemoteDevice': grpc.unary_unary_rpc_method_handler(servicer.AddRemoteDevice, request_deserializer=ares__devices__pb2.AddRemoteDeviceRequest.FromString, response_serializer=ares__devices__pb2.AddRemoteDeviceResponse.SerializeToString), 'RemoveRemoteDevice': grpc.unary_unary_rpc_method_handler(servicer.RemoveRemoteDevice, request_deserializer=ares__devices__pb2.RemoveRemoteDeviceRequest.FromString, response_serializer=ares__devices__pb2.RemoveRemoteDeviceResponse.SerializeToString), 'UpdateRemoteDevice': grpc.unary_unary_rpc_method_handler(servicer.UpdateRemoteDevice, request_deserializer=ares__devices__pb2.UpdateRemoteDeviceRequest.FromString, response_serializer=ares__devices__pb2.UpdateRemoteDeviceResponse.SerializeToString), 'GetAllRemoteDevicesConfigs': grpc.unary_unary_rpc_method_handler(servicer.GetAllRemoteDevicesConfigs, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=ares__devices__pb2.RemoteDeviceConfigResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('ares.services.device.AresDevices', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('ares.services.device.AresDevices', rpc_method_handlers)

class AresDevices(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ListAresDevices(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/ListAresDevices', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, ares__devices__pb2.ListAresDevicesResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetDeviceInfo(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetDeviceInfo', ares__devices__pb2.DeviceInfoRequest.SerializeToString, device_dot_device__info__pb2.DeviceInfo.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetServerSerialPorts(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetServerSerialPorts', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, ares__devices__pb2.ListServerSerialPortsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetDeviceStatus(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetDeviceStatus', ares__devices__pb2.DeviceStatusRequest.SerializeToString, device_dot_device__status__pb2.DeviceOperationalStatus.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetCommandMetadatas(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetCommandMetadatas', ares__devices__pb2.CommandMetadatasRequest.SerializeToString, ares__devices__pb2.CommandMetadatasResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ExecuteCommand(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/ExecuteCommand', templates_dot_command__template__pb2.CommandTemplate.SerializeToString, device_dot_device__execution__result__pb2.DeviceExecutionResult.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetAllDeviceConfigs(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetAllDeviceConfigs', ares__devices__pb2.DeviceConfigRequest.SerializeToString, ares__devices__pb2.DeviceConfigResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Activate(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/Activate', ares__devices__pb2.DeviceActivateRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def SetDeviceSettings(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/SetDeviceSettings', device_dot_device__settings__pb2.DeviceSettings.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetDeviceSettings(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetDeviceSettings', ares__devices__pb2.DeviceSettingsRequest.SerializeToString, ares__struct__pb2.AresStruct.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetDeviceState(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetDeviceState', ares__devices__pb2.DeviceStateRequest.SerializeToString, ares__devices__pb2.DeviceStateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetDeviceStateStream(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_stream(request, target, '/ares.services.device.AresDevices/GetDeviceStateStream', ares__devices__pb2.DeviceStateStreamRequest.SerializeToString, ares__devices__pb2.DeviceStateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetDeviceStateSchema(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetDeviceStateSchema', ares__devices__pb2.DeviceStateSchemaRequest.SerializeToString, ares__devices__pb2.DeviceStateSchemaResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def SetDeviceLoggerSettings(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/SetDeviceLoggerSettings', device_dot_device__logging__settings__pb2.DeviceLoggingSettings.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetDeviceLoggerSettings(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetDeviceLoggerSettings', ares__devices__pb2.DeviceLoggerSettingsRequest.SerializeToString, device_dot_device__logging__settings__pb2.DeviceLoggingSettings.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetDeviceLoggers(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetDeviceLoggers', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, ares__devices__pb2.DeviceLoggersResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ListRemoteAresDevices(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/ListRemoteAresDevices', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, ares__devices__pb2.ListAresRemoteDevicesResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def AddRemoteDevice(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/AddRemoteDevice', ares__devices__pb2.AddRemoteDeviceRequest.SerializeToString, ares__devices__pb2.AddRemoteDeviceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RemoveRemoteDevice(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/RemoveRemoteDevice', ares__devices__pb2.RemoveRemoteDeviceRequest.SerializeToString, ares__devices__pb2.RemoveRemoteDeviceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def UpdateRemoteDevice(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/UpdateRemoteDevice', ares__devices__pb2.UpdateRemoteDeviceRequest.SerializeToString, ares__devices__pb2.UpdateRemoteDeviceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetAllRemoteDevicesConfigs(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ares.services.device.AresDevices/GetAllRemoteDevicesConfigs', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, ares__devices__pb2.RemoteDeviceConfigResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)