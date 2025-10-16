import datetime

from buf.validate import validate_pb2 as _validate_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from metalstack.api.v2 import common_pb2 as _common_pb2
from metalstack.api.v2 import predefined_rules_pb2 as _predefined_rules_pb2
from metalstack.api.v2 import switch_pb2 as _switch_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
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

class SwitchServiceListRequest(_message.Message):
    __slots__ = ("query",)
    QUERY_FIELD_NUMBER: _ClassVar[int]
    query: _switch_pb2.SwitchQuery
    def __init__(self, query: _Optional[_Union[_switch_pb2.SwitchQuery, _Mapping]] = ...) -> None: ...

class SwitchServiceListResponse(_message.Message):
    __slots__ = ("switches",)
    SWITCHES_FIELD_NUMBER: _ClassVar[int]
    switches: _containers.RepeatedCompositeFieldContainer[_switch_pb2.Switch]
    def __init__(self, switches: _Optional[_Iterable[_Union[_switch_pb2.Switch, _Mapping]]] = ...) -> None: ...

class SwitchServiceUpdateRequest(_message.Message):
    __slots__ = ("id", "update_meta", "updated_at", "description", "replace_mode", "management_ip", "management_user", "console_command", "nics", "os")
    ID_FIELD_NUMBER: _ClassVar[int]
    UPDATE_META_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    REPLACE_MODE_FIELD_NUMBER: _ClassVar[int]
    MANAGEMENT_IP_FIELD_NUMBER: _ClassVar[int]
    MANAGEMENT_USER_FIELD_NUMBER: _ClassVar[int]
    CONSOLE_COMMAND_FIELD_NUMBER: _ClassVar[int]
    NICS_FIELD_NUMBER: _ClassVar[int]
    OS_FIELD_NUMBER: _ClassVar[int]
    id: str
    update_meta: _common_pb2.UpdateMeta
    updated_at: _timestamp_pb2.Timestamp
    description: str
    replace_mode: _switch_pb2.SwitchReplaceMode
    management_ip: str
    management_user: str
    console_command: str
    nics: _containers.RepeatedCompositeFieldContainer[_switch_pb2.SwitchNic]
    os: _switch_pb2.SwitchOS
    def __init__(self, id: _Optional[str] = ..., update_meta: _Optional[_Union[_common_pb2.UpdateMeta, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., description: _Optional[str] = ..., replace_mode: _Optional[_Union[_switch_pb2.SwitchReplaceMode, str]] = ..., management_ip: _Optional[str] = ..., management_user: _Optional[str] = ..., console_command: _Optional[str] = ..., nics: _Optional[_Iterable[_Union[_switch_pb2.SwitchNic, _Mapping]]] = ..., os: _Optional[_Union[_switch_pb2.SwitchOS, _Mapping]] = ...) -> None: ...

class SwitchServiceUpdateResponse(_message.Message):
    __slots__ = ("switch",)
    SWITCH_FIELD_NUMBER: _ClassVar[int]
    switch: _switch_pb2.Switch
    def __init__(self, switch: _Optional[_Union[_switch_pb2.Switch, _Mapping]] = ...) -> None: ...

class SwitchServiceDeleteRequest(_message.Message):
    __slots__ = ("id", "force")
    ID_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    id: str
    force: bool
    def __init__(self, id: _Optional[str] = ..., force: _Optional[bool] = ...) -> None: ...

class SwitchServiceDeleteResponse(_message.Message):
    __slots__ = ("switch",)
    SWITCH_FIELD_NUMBER: _ClassVar[int]
    switch: _switch_pb2.Switch
    def __init__(self, switch: _Optional[_Union[_switch_pb2.Switch, _Mapping]] = ...) -> None: ...

class SwitchServiceMigrateRequest(_message.Message):
    __slots__ = ("old_switch", "new_switch")
    OLD_SWITCH_FIELD_NUMBER: _ClassVar[int]
    NEW_SWITCH_FIELD_NUMBER: _ClassVar[int]
    old_switch: str
    new_switch: str
    def __init__(self, old_switch: _Optional[str] = ..., new_switch: _Optional[str] = ...) -> None: ...

class SwitchServiceMigrateResponse(_message.Message):
    __slots__ = ("switch",)
    SWITCH_FIELD_NUMBER: _ClassVar[int]
    switch: _switch_pb2.Switch
    def __init__(self, switch: _Optional[_Union[_switch_pb2.Switch, _Mapping]] = ...) -> None: ...

class SwitchServicePortRequest(_message.Message):
    __slots__ = ("id", "nic_name", "status")
    ID_FIELD_NUMBER: _ClassVar[int]
    NIC_NAME_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    id: str
    nic_name: str
    status: _switch_pb2.SwitchPortStatus
    def __init__(self, id: _Optional[str] = ..., nic_name: _Optional[str] = ..., status: _Optional[_Union[_switch_pb2.SwitchPortStatus, str]] = ...) -> None: ...

class SwitchServicePortResponse(_message.Message):
    __slots__ = ("switch",)
    SWITCH_FIELD_NUMBER: _ClassVar[int]
    switch: _switch_pb2.Switch
    def __init__(self, switch: _Optional[_Union[_switch_pb2.Switch, _Mapping]] = ...) -> None: ...
