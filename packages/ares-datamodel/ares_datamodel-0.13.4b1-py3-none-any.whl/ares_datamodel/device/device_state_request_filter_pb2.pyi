import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceStateRequestFilter(_message.Message):
    __slots__ = ("start", "end", "completed_experiment_id", "completed_campaign_id", "interval", "device_ids")
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_CAMPAIGN_ID_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_FIELD_NUMBER: _ClassVar[int]
    DEVICE_IDS_FIELD_NUMBER: _ClassVar[int]
    start: _timestamp_pb2.Timestamp
    end: _timestamp_pb2.Timestamp
    completed_experiment_id: _wrappers_pb2.StringValue
    completed_campaign_id: _wrappers_pb2.StringValue
    interval: _duration_pb2.Duration
    device_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, start: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., completed_experiment_id: _Optional[_Union[_wrappers_pb2.StringValue, _Mapping]] = ..., completed_campaign_id: _Optional[_Union[_wrappers_pb2.StringValue, _Mapping]] = ..., interval: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., device_ids: _Optional[_Iterable[str]] = ...) -> None: ...
