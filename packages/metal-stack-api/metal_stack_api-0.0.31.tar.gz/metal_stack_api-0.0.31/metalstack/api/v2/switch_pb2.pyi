import datetime

from buf.validate import validate_pb2 as _validate_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from metalstack.api.v2 import common_pb2 as _common_pb2
from metalstack.api.v2 import predefined_rules_pb2 as _predefined_rules_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BGPState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BGP_STATE_UNSPECIFIED: _ClassVar[BGPState]
    BGP_STATE_IDLE: _ClassVar[BGPState]
    BGP_STATE_CONNECT: _ClassVar[BGPState]
    BGP_STATE_ACTIVE: _ClassVar[BGPState]
    BGP_STATE_OPEN_SENT: _ClassVar[BGPState]
    BGP_STATE_OPEN_CONFIRM: _ClassVar[BGPState]
    BGP_STATE_ESTABLISHED: _ClassVar[BGPState]

class SwitchReplaceMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SWITCH_REPLACE_MODE_UNSPECIFIED: _ClassVar[SwitchReplaceMode]
    SWITCH_REPLACE_MODE_REPLACE: _ClassVar[SwitchReplaceMode]
    SWITCH_REPLACE_MODE_OPERATIONAL: _ClassVar[SwitchReplaceMode]

class SwitchOSVendor(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SWITCH_OS_VENDOR_UNSPECIFIED: _ClassVar[SwitchOSVendor]
    SWITCH_OS_VENDOR_CUMULUS: _ClassVar[SwitchOSVendor]
    SWITCH_OS_VENDOR_SONIC: _ClassVar[SwitchOSVendor]

class SwitchPortStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SWITCH_PORT_STATUS_UNSPECIFIED: _ClassVar[SwitchPortStatus]
    SWITCH_PORT_STATUS_UP: _ClassVar[SwitchPortStatus]
    SWITCH_PORT_STATUS_DOWN: _ClassVar[SwitchPortStatus]
    SWITCH_PORT_STATUS_UNKNOWN: _ClassVar[SwitchPortStatus]
BGP_STATE_UNSPECIFIED: BGPState
BGP_STATE_IDLE: BGPState
BGP_STATE_CONNECT: BGPState
BGP_STATE_ACTIVE: BGPState
BGP_STATE_OPEN_SENT: BGPState
BGP_STATE_OPEN_CONFIRM: BGPState
BGP_STATE_ESTABLISHED: BGPState
SWITCH_REPLACE_MODE_UNSPECIFIED: SwitchReplaceMode
SWITCH_REPLACE_MODE_REPLACE: SwitchReplaceMode
SWITCH_REPLACE_MODE_OPERATIONAL: SwitchReplaceMode
SWITCH_OS_VENDOR_UNSPECIFIED: SwitchOSVendor
SWITCH_OS_VENDOR_CUMULUS: SwitchOSVendor
SWITCH_OS_VENDOR_SONIC: SwitchOSVendor
SWITCH_PORT_STATUS_UNSPECIFIED: SwitchPortStatus
SWITCH_PORT_STATUS_UP: SwitchPortStatus
SWITCH_PORT_STATUS_DOWN: SwitchPortStatus
SWITCH_PORT_STATUS_UNKNOWN: SwitchPortStatus

class Switch(_message.Message):
    __slots__ = ("id", "meta", "description", "rack", "partition", "replace_mode", "management_ip", "management_user", "console_command", "nics", "os", "machine_connections")
    ID_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    RACK_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    REPLACE_MODE_FIELD_NUMBER: _ClassVar[int]
    MANAGEMENT_IP_FIELD_NUMBER: _ClassVar[int]
    MANAGEMENT_USER_FIELD_NUMBER: _ClassVar[int]
    CONSOLE_COMMAND_FIELD_NUMBER: _ClassVar[int]
    NICS_FIELD_NUMBER: _ClassVar[int]
    OS_FIELD_NUMBER: _ClassVar[int]
    MACHINE_CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    id: str
    meta: _common_pb2.Meta
    description: str
    rack: str
    partition: str
    replace_mode: SwitchReplaceMode
    management_ip: str
    management_user: str
    console_command: str
    nics: _containers.RepeatedCompositeFieldContainer[SwitchNic]
    os: SwitchOS
    machine_connections: _containers.RepeatedCompositeFieldContainer[MachineConnection]
    def __init__(self, id: _Optional[str] = ..., meta: _Optional[_Union[_common_pb2.Meta, _Mapping]] = ..., description: _Optional[str] = ..., rack: _Optional[str] = ..., partition: _Optional[str] = ..., replace_mode: _Optional[_Union[SwitchReplaceMode, str]] = ..., management_ip: _Optional[str] = ..., management_user: _Optional[str] = ..., console_command: _Optional[str] = ..., nics: _Optional[_Iterable[_Union[SwitchNic, _Mapping]]] = ..., os: _Optional[_Union[SwitchOS, _Mapping]] = ..., machine_connections: _Optional[_Iterable[_Union[MachineConnection, _Mapping]]] = ...) -> None: ...

class SwitchOS(_message.Message):
    __slots__ = ("vendor", "version", "metal_core_version")
    VENDOR_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    METAL_CORE_VERSION_FIELD_NUMBER: _ClassVar[int]
    vendor: SwitchOSVendor
    version: str
    metal_core_version: str
    def __init__(self, vendor: _Optional[_Union[SwitchOSVendor, str]] = ..., version: _Optional[str] = ..., metal_core_version: _Optional[str] = ...) -> None: ...

class SwitchNic(_message.Message):
    __slots__ = ("name", "identifier", "mac", "vrf", "state", "bgp_filter", "bgp_port_state")
    NAME_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    MAC_FIELD_NUMBER: _ClassVar[int]
    VRF_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    BGP_FILTER_FIELD_NUMBER: _ClassVar[int]
    BGP_PORT_STATE_FIELD_NUMBER: _ClassVar[int]
    name: str
    identifier: str
    mac: str
    vrf: str
    state: NicState
    bgp_filter: BGPFilter
    bgp_port_state: SwitchBGPPortState
    def __init__(self, name: _Optional[str] = ..., identifier: _Optional[str] = ..., mac: _Optional[str] = ..., vrf: _Optional[str] = ..., state: _Optional[_Union[NicState, _Mapping]] = ..., bgp_filter: _Optional[_Union[BGPFilter, _Mapping]] = ..., bgp_port_state: _Optional[_Union[SwitchBGPPortState, _Mapping]] = ...) -> None: ...

class BGPFilter(_message.Message):
    __slots__ = ("cidrs", "vnis")
    CIDRS_FIELD_NUMBER: _ClassVar[int]
    VNIS_FIELD_NUMBER: _ClassVar[int]
    cidrs: _containers.RepeatedScalarFieldContainer[str]
    vnis: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, cidrs: _Optional[_Iterable[str]] = ..., vnis: _Optional[_Iterable[str]] = ...) -> None: ...

class SwitchBGPPortState(_message.Message):
    __slots__ = ("neighbor", "peer_group", "vrf_name", "bgp_state", "bgp_timer_up_established", "sent_prefix_counter", "accepted_prefix_counter")
    NEIGHBOR_FIELD_NUMBER: _ClassVar[int]
    PEER_GROUP_FIELD_NUMBER: _ClassVar[int]
    VRF_NAME_FIELD_NUMBER: _ClassVar[int]
    BGP_STATE_FIELD_NUMBER: _ClassVar[int]
    BGP_TIMER_UP_ESTABLISHED_FIELD_NUMBER: _ClassVar[int]
    SENT_PREFIX_COUNTER_FIELD_NUMBER: _ClassVar[int]
    ACCEPTED_PREFIX_COUNTER_FIELD_NUMBER: _ClassVar[int]
    neighbor: str
    peer_group: str
    vrf_name: str
    bgp_state: BGPState
    bgp_timer_up_established: _timestamp_pb2.Timestamp
    sent_prefix_counter: int
    accepted_prefix_counter: int
    def __init__(self, neighbor: _Optional[str] = ..., peer_group: _Optional[str] = ..., vrf_name: _Optional[str] = ..., bgp_state: _Optional[_Union[BGPState, str]] = ..., bgp_timer_up_established: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., sent_prefix_counter: _Optional[int] = ..., accepted_prefix_counter: _Optional[int] = ...) -> None: ...

class NicState(_message.Message):
    __slots__ = ("desired", "actual")
    DESIRED_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_FIELD_NUMBER: _ClassVar[int]
    desired: SwitchPortStatus
    actual: SwitchPortStatus
    def __init__(self, desired: _Optional[_Union[SwitchPortStatus, str]] = ..., actual: _Optional[_Union[SwitchPortStatus, str]] = ...) -> None: ...

class MachineConnection(_message.Message):
    __slots__ = ("machine_id", "nic")
    MACHINE_ID_FIELD_NUMBER: _ClassVar[int]
    NIC_FIELD_NUMBER: _ClassVar[int]
    machine_id: str
    nic: SwitchNic
    def __init__(self, machine_id: _Optional[str] = ..., nic: _Optional[_Union[SwitchNic, _Mapping]] = ...) -> None: ...

class SwitchQuery(_message.Message):
    __slots__ = ("id", "partition", "rack", "os")
    ID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    RACK_FIELD_NUMBER: _ClassVar[int]
    OS_FIELD_NUMBER: _ClassVar[int]
    id: str
    partition: str
    rack: str
    os: SwitchOSQuery
    def __init__(self, id: _Optional[str] = ..., partition: _Optional[str] = ..., rack: _Optional[str] = ..., os: _Optional[_Union[SwitchOSQuery, _Mapping]] = ...) -> None: ...

class SwitchOSQuery(_message.Message):
    __slots__ = ("vendor", "version")
    VENDOR_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    vendor: SwitchOSVendor
    version: str
    def __init__(self, vendor: _Optional[_Union[SwitchOSVendor, str]] = ..., version: _Optional[str] = ...) -> None: ...
