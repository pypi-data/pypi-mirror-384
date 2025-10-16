import datetime

from buf.validate import validate_pb2 as _validate_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from metalstack.api.v2 import common_pb2 as _common_pb2
from metalstack.api.v2 import image_pb2 as _image_pb2
from metalstack.api.v2 import predefined_rules_pb2 as _predefined_rules_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ImageServiceCreateRequest(_message.Message):
    __slots__ = ("image",)
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    image: _image_pb2.Image
    def __init__(self, image: _Optional[_Union[_image_pb2.Image, _Mapping]] = ...) -> None: ...

class ImageServiceCreateResponse(_message.Message):
    __slots__ = ("image",)
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    image: _image_pb2.Image
    def __init__(self, image: _Optional[_Union[_image_pb2.Image, _Mapping]] = ...) -> None: ...

class ImageServiceUpdateRequest(_message.Message):
    __slots__ = ("id", "update_meta", "url", "name", "description", "features", "classification", "expires_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    UPDATE_META_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    CLASSIFICATION_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    update_meta: _common_pb2.UpdateMeta
    url: str
    name: str
    description: str
    features: _containers.RepeatedScalarFieldContainer[_image_pb2.ImageFeature]
    classification: _image_pb2.ImageClassification
    expires_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., update_meta: _Optional[_Union[_common_pb2.UpdateMeta, _Mapping]] = ..., url: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., features: _Optional[_Iterable[_Union[_image_pb2.ImageFeature, str]]] = ..., classification: _Optional[_Union[_image_pb2.ImageClassification, str]] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ImageServiceUpdateResponse(_message.Message):
    __slots__ = ("image",)
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    image: _image_pb2.Image
    def __init__(self, image: _Optional[_Union[_image_pb2.Image, _Mapping]] = ...) -> None: ...

class ImageServiceDeleteRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ImageServiceDeleteResponse(_message.Message):
    __slots__ = ("image",)
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    image: _image_pb2.Image
    def __init__(self, image: _Optional[_Union[_image_pb2.Image, _Mapping]] = ...) -> None: ...

class ImageServiceUsageRequest(_message.Message):
    __slots__ = ("query",)
    QUERY_FIELD_NUMBER: _ClassVar[int]
    query: _image_pb2.ImageQuery
    def __init__(self, query: _Optional[_Union[_image_pb2.ImageQuery, _Mapping]] = ...) -> None: ...

class ImageServiceUsageResponse(_message.Message):
    __slots__ = ("image_usage",)
    IMAGE_USAGE_FIELD_NUMBER: _ClassVar[int]
    image_usage: _containers.RepeatedCompositeFieldContainer[_image_pb2.ImageUsage]
    def __init__(self, image_usage: _Optional[_Iterable[_Union[_image_pb2.ImageUsage, _Mapping]]] = ...) -> None: ...
