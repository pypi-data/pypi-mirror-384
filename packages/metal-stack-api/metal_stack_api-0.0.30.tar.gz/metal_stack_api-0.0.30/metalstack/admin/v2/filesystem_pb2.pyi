from buf.validate import validate_pb2 as _validate_pb2
from metalstack.api.v2 import common_pb2 as _common_pb2
from metalstack.api.v2 import filesystem_pb2 as _filesystem_pb2
from metalstack.api.v2 import predefined_rules_pb2 as _predefined_rules_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class FilesystemServiceCreateRequest(_message.Message):
    __slots__ = ("filesystem_layout",)
    FILESYSTEM_LAYOUT_FIELD_NUMBER: _ClassVar[int]
    filesystem_layout: _filesystem_pb2.FilesystemLayout
    def __init__(self, filesystem_layout: _Optional[_Union[_filesystem_pb2.FilesystemLayout, _Mapping]] = ...) -> None: ...

class FilesystemServiceCreateResponse(_message.Message):
    __slots__ = ("filesystem_layout",)
    FILESYSTEM_LAYOUT_FIELD_NUMBER: _ClassVar[int]
    filesystem_layout: _filesystem_pb2.FilesystemLayout
    def __init__(self, filesystem_layout: _Optional[_Union[_filesystem_pb2.FilesystemLayout, _Mapping]] = ...) -> None: ...

class FilesystemServiceUpdateRequest(_message.Message):
    __slots__ = ("id", "update_meta", "name", "description", "filesystems", "disks", "raid", "volume_groups", "logical_volumes", "constraints")
    ID_FIELD_NUMBER: _ClassVar[int]
    UPDATE_META_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    FILESYSTEMS_FIELD_NUMBER: _ClassVar[int]
    DISKS_FIELD_NUMBER: _ClassVar[int]
    RAID_FIELD_NUMBER: _ClassVar[int]
    VOLUME_GROUPS_FIELD_NUMBER: _ClassVar[int]
    LOGICAL_VOLUMES_FIELD_NUMBER: _ClassVar[int]
    CONSTRAINTS_FIELD_NUMBER: _ClassVar[int]
    id: str
    update_meta: _common_pb2.UpdateMeta
    name: str
    description: str
    filesystems: _containers.RepeatedCompositeFieldContainer[_filesystem_pb2.Filesystem]
    disks: _containers.RepeatedCompositeFieldContainer[_filesystem_pb2.Disk]
    raid: _containers.RepeatedCompositeFieldContainer[_filesystem_pb2.Raid]
    volume_groups: _containers.RepeatedCompositeFieldContainer[_filesystem_pb2.VolumeGroup]
    logical_volumes: _containers.RepeatedCompositeFieldContainer[_filesystem_pb2.LogicalVolume]
    constraints: _filesystem_pb2.FilesystemLayoutConstraints
    def __init__(self, id: _Optional[str] = ..., update_meta: _Optional[_Union[_common_pb2.UpdateMeta, _Mapping]] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., filesystems: _Optional[_Iterable[_Union[_filesystem_pb2.Filesystem, _Mapping]]] = ..., disks: _Optional[_Iterable[_Union[_filesystem_pb2.Disk, _Mapping]]] = ..., raid: _Optional[_Iterable[_Union[_filesystem_pb2.Raid, _Mapping]]] = ..., volume_groups: _Optional[_Iterable[_Union[_filesystem_pb2.VolumeGroup, _Mapping]]] = ..., logical_volumes: _Optional[_Iterable[_Union[_filesystem_pb2.LogicalVolume, _Mapping]]] = ..., constraints: _Optional[_Union[_filesystem_pb2.FilesystemLayoutConstraints, _Mapping]] = ...) -> None: ...

class FilesystemServiceUpdateResponse(_message.Message):
    __slots__ = ("filesystem_layout",)
    FILESYSTEM_LAYOUT_FIELD_NUMBER: _ClassVar[int]
    filesystem_layout: _filesystem_pb2.FilesystemLayout
    def __init__(self, filesystem_layout: _Optional[_Union[_filesystem_pb2.FilesystemLayout, _Mapping]] = ...) -> None: ...

class FilesystemServiceDeleteRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class FilesystemServiceDeleteResponse(_message.Message):
    __slots__ = ("filesystem_layout",)
    FILESYSTEM_LAYOUT_FIELD_NUMBER: _ClassVar[int]
    filesystem_layout: _filesystem_pb2.FilesystemLayout
    def __init__(self, filesystem_layout: _Optional[_Union[_filesystem_pb2.FilesystemLayout, _Mapping]] = ...) -> None: ...
