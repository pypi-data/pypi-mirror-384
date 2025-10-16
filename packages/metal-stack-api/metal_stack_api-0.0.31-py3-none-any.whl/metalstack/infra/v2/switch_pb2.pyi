import datetime

from buf.validate import validate_pb2 as _validate_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from metalstack.api.v2 import common_pb2 as _common_pb2
from metalstack.api.v2 import predefined_rules_pb2 as _predefined_rules_pb2
from metalstack.api.v2 import switch_pb2 as _switch_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SwitchServiceGetRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class SwitchServiceGetResponse(_message.Message):
    __slots__ = ("switch",)
    SWITCH_FIELD_NUMBER: _ClassVar[int]
    switch: _switch_pb2.Switch
    def __init__(self, switch: _Optional[_Union[_switch_pb2.Switch, _Mapping]] = ...) -> None: ...

class SwitchServiceRegisterRequest(_message.Message):
    __slots__ = ("switch",)
    SWITCH_FIELD_NUMBER: _ClassVar[int]
    switch: _switch_pb2.Switch
    def __init__(self, switch: _Optional[_Union[_switch_pb2.Switch, _Mapping]] = ...) -> None: ...

class SwitchServiceRegisterResponse(_message.Message):
    __slots__ = ("switch",)
    SWITCH_FIELD_NUMBER: _ClassVar[int]
    switch: _switch_pb2.Switch
    def __init__(self, switch: _Optional[_Union[_switch_pb2.Switch, _Mapping]] = ...) -> None: ...

class SwitchServiceHeartbeatRequest(_message.Message):
    __slots__ = ("id", "duration", "error", "port_states", "bgp_port_states")
    class PortStatesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _switch_pb2.SwitchPortStatus
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_switch_pb2.SwitchPortStatus, str]] = ...) -> None: ...
    class BgpPortStatesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _switch_pb2.SwitchBGPPortState
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_switch_pb2.SwitchBGPPortState, _Mapping]] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    PORT_STATES_FIELD_NUMBER: _ClassVar[int]
    BGP_PORT_STATES_FIELD_NUMBER: _ClassVar[int]
    id: str
    duration: _duration_pb2.Duration
    error: str
    port_states: _containers.ScalarMap[str, _switch_pb2.SwitchPortStatus]
    bgp_port_states: _containers.MessageMap[str, _switch_pb2.SwitchBGPPortState]
    def __init__(self, id: _Optional[str] = ..., duration: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., error: _Optional[str] = ..., port_states: _Optional[_Mapping[str, _switch_pb2.SwitchPortStatus]] = ..., bgp_port_states: _Optional[_Mapping[str, _switch_pb2.SwitchBGPPortState]] = ...) -> None: ...

class SwitchServiceHeartbeatResponse(_message.Message):
    __slots__ = ("id", "last_sync", "last_sync_error")
    ID_FIELD_NUMBER: _ClassVar[int]
    LAST_SYNC_FIELD_NUMBER: _ClassVar[int]
    LAST_SYNC_ERROR_FIELD_NUMBER: _ClassVar[int]
    id: str
    last_sync: SwitchSync
    last_sync_error: SwitchSync
    def __init__(self, id: _Optional[str] = ..., last_sync: _Optional[_Union[SwitchSync, _Mapping]] = ..., last_sync_error: _Optional[_Union[SwitchSync, _Mapping]] = ...) -> None: ...

class SwitchSync(_message.Message):
    __slots__ = ("time", "duration", "error")
    TIME_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    time: _timestamp_pb2.Timestamp
    duration: _duration_pb2.Duration
    error: str
    def __init__(self, time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., duration: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., error: _Optional[str] = ...) -> None: ...
