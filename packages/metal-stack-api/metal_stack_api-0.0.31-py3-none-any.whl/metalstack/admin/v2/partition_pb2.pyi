from buf.validate import validate_pb2 as _validate_pb2
from metalstack.api.v2 import common_pb2 as _common_pb2
from metalstack.api.v2 import partition_pb2 as _partition_pb2
from metalstack.api.v2 import predefined_rules_pb2 as _predefined_rules_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PartitionServiceCreateRequest(_message.Message):
    __slots__ = ("partition",)
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    partition: _partition_pb2.Partition
    def __init__(self, partition: _Optional[_Union[_partition_pb2.Partition, _Mapping]] = ...) -> None: ...

class PartitionServiceUpdateRequest(_message.Message):
    __slots__ = ("id", "update_meta", "description", "boot_configuration", "dns_server", "ntp_server", "mgmt_service_addresses", "labels")
    ID_FIELD_NUMBER: _ClassVar[int]
    UPDATE_META_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    BOOT_CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    DNS_SERVER_FIELD_NUMBER: _ClassVar[int]
    NTP_SERVER_FIELD_NUMBER: _ClassVar[int]
    MGMT_SERVICE_ADDRESSES_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    id: str
    update_meta: _common_pb2.UpdateMeta
    description: str
    boot_configuration: _partition_pb2.PartitionBootConfiguration
    dns_server: _containers.RepeatedCompositeFieldContainer[_partition_pb2.DNSServer]
    ntp_server: _containers.RepeatedCompositeFieldContainer[_partition_pb2.NTPServer]
    mgmt_service_addresses: _containers.RepeatedScalarFieldContainer[str]
    labels: _common_pb2.UpdateLabels
    def __init__(self, id: _Optional[str] = ..., update_meta: _Optional[_Union[_common_pb2.UpdateMeta, _Mapping]] = ..., description: _Optional[str] = ..., boot_configuration: _Optional[_Union[_partition_pb2.PartitionBootConfiguration, _Mapping]] = ..., dns_server: _Optional[_Iterable[_Union[_partition_pb2.DNSServer, _Mapping]]] = ..., ntp_server: _Optional[_Iterable[_Union[_partition_pb2.NTPServer, _Mapping]]] = ..., mgmt_service_addresses: _Optional[_Iterable[str]] = ..., labels: _Optional[_Union[_common_pb2.UpdateLabels, _Mapping]] = ...) -> None: ...

class PartitionServiceDeleteRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class PartitionServiceCreateResponse(_message.Message):
    __slots__ = ("partition",)
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    partition: _partition_pb2.Partition
    def __init__(self, partition: _Optional[_Union[_partition_pb2.Partition, _Mapping]] = ...) -> None: ...

class PartitionServiceUpdateResponse(_message.Message):
    __slots__ = ("partition",)
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    partition: _partition_pb2.Partition
    def __init__(self, partition: _Optional[_Union[_partition_pb2.Partition, _Mapping]] = ...) -> None: ...

class PartitionServiceDeleteResponse(_message.Message):
    __slots__ = ("partition",)
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    partition: _partition_pb2.Partition
    def __init__(self, partition: _Optional[_Union[_partition_pb2.Partition, _Mapping]] = ...) -> None: ...

class PartitionServiceCapacityRequest(_message.Message):
    __slots__ = ("id", "size", "project")
    ID_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    PROJECT_FIELD_NUMBER: _ClassVar[int]
    id: str
    size: str
    project: str
    def __init__(self, id: _Optional[str] = ..., size: _Optional[str] = ..., project: _Optional[str] = ...) -> None: ...

class PartitionServiceCapacityResponse(_message.Message):
    __slots__ = ("size", "total", "phoned_home", "waiting", "other", "other_machines", "allocated", "allocatable", "free", "unavailable", "faulty", "faulty_machines", "reservations", "used_reservations", "remaining_reservations")
    SIZE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    PHONED_HOME_FIELD_NUMBER: _ClassVar[int]
    WAITING_FIELD_NUMBER: _ClassVar[int]
    OTHER_FIELD_NUMBER: _ClassVar[int]
    OTHER_MACHINES_FIELD_NUMBER: _ClassVar[int]
    ALLOCATED_FIELD_NUMBER: _ClassVar[int]
    ALLOCATABLE_FIELD_NUMBER: _ClassVar[int]
    FREE_FIELD_NUMBER: _ClassVar[int]
    UNAVAILABLE_FIELD_NUMBER: _ClassVar[int]
    FAULTY_FIELD_NUMBER: _ClassVar[int]
    FAULTY_MACHINES_FIELD_NUMBER: _ClassVar[int]
    RESERVATIONS_FIELD_NUMBER: _ClassVar[int]
    USED_RESERVATIONS_FIELD_NUMBER: _ClassVar[int]
    REMAINING_RESERVATIONS_FIELD_NUMBER: _ClassVar[int]
    size: str
    total: int
    phoned_home: int
    waiting: int
    other: int
    other_machines: _containers.RepeatedScalarFieldContainer[str]
    allocated: int
    allocatable: int
    free: int
    unavailable: int
    faulty: int
    faulty_machines: _containers.RepeatedScalarFieldContainer[str]
    reservations: int
    used_reservations: int
    remaining_reservations: int
    def __init__(self, size: _Optional[str] = ..., total: _Optional[int] = ..., phoned_home: _Optional[int] = ..., waiting: _Optional[int] = ..., other: _Optional[int] = ..., other_machines: _Optional[_Iterable[str]] = ..., allocated: _Optional[int] = ..., allocatable: _Optional[int] = ..., free: _Optional[int] = ..., unavailable: _Optional[int] = ..., faulty: _Optional[int] = ..., faulty_machines: _Optional[_Iterable[str]] = ..., reservations: _Optional[int] = ..., used_reservations: _Optional[int] = ..., remaining_reservations: _Optional[int] = ...) -> None: ...
