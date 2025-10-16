from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ObjectSource(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OBJECT_SOURCE_MEMORY: _ClassVar[ObjectSource]
    OBJECT_SOURCE_DISK: _ClassVar[ObjectSource]
    OBJECT_SOURCE_DENKCACHE: _ClassVar[ObjectSource]
    OBJECT_SOURCE_AZURE: _ClassVar[ObjectSource]

class GetObjectCachePolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GET_OBJECT_MEMORY_ONLY: _ClassVar[GetObjectCachePolicy]
    GET_OBJECT_DISK_ONLY: _ClassVar[GetObjectCachePolicy]
    GET_OBJECT_MEMORY_AND_DISK: _ClassVar[GetObjectCachePolicy]
    GET_OBJECT_NO_CACHE: _ClassVar[GetObjectCachePolicy]

class CacheObjectPolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CACHE_OBJECT_MEMORY_ONLY: _ClassVar[CacheObjectPolicy]
    CACHE_OBJECT_DISK_ONLY: _ClassVar[CacheObjectPolicy]
    CACHE_OBJECT_MEMORY_AND_DISK: _ClassVar[CacheObjectPolicy]
OBJECT_SOURCE_MEMORY: ObjectSource
OBJECT_SOURCE_DISK: ObjectSource
OBJECT_SOURCE_DENKCACHE: ObjectSource
OBJECT_SOURCE_AZURE: ObjectSource
GET_OBJECT_MEMORY_ONLY: GetObjectCachePolicy
GET_OBJECT_DISK_ONLY: GetObjectCachePolicy
GET_OBJECT_MEMORY_AND_DISK: GetObjectCachePolicy
GET_OBJECT_NO_CACHE: GetObjectCachePolicy
CACHE_OBJECT_MEMORY_ONLY: CacheObjectPolicy
CACHE_OBJECT_DISK_ONLY: CacheObjectPolicy
CACHE_OBJECT_MEMORY_AND_DISK: CacheObjectPolicy

class ObjectExistsRequest(_message.Message):
    __slots__ = ("container_name", "blob_name")
    CONTAINER_NAME_FIELD_NUMBER: _ClassVar[int]
    BLOB_NAME_FIELD_NUMBER: _ClassVar[int]
    container_name: str
    blob_name: str
    def __init__(self, container_name: _Optional[str] = ..., blob_name: _Optional[str] = ...) -> None: ...

class ObjectExistsResponse(_message.Message):
    __slots__ = ("exists",)
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    exists: bool
    def __init__(self, exists: bool = ...) -> None: ...

class ObjectSourceMessage(_message.Message):
    __slots__ = ("source", "source_info")
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_INFO_FIELD_NUMBER: _ClassVar[int]
    source: ObjectSource
    source_info: str
    def __init__(self, source: _Optional[_Union[ObjectSource, str]] = ..., source_info: _Optional[str] = ...) -> None: ...

class GetObjectRequest(_message.Message):
    __slots__ = ("container_name", "blob_name", "cache_policy")
    CONTAINER_NAME_FIELD_NUMBER: _ClassVar[int]
    BLOB_NAME_FIELD_NUMBER: _ClassVar[int]
    CACHE_POLICY_FIELD_NUMBER: _ClassVar[int]
    container_name: str
    blob_name: str
    cache_policy: GetObjectCachePolicy
    def __init__(self, container_name: _Optional[str] = ..., blob_name: _Optional[str] = ..., cache_policy: _Optional[_Union[GetObjectCachePolicy, str]] = ...) -> None: ...

class GetObjectResponse(_message.Message):
    __slots__ = ("object", "source")
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    object: bytes
    source: ObjectSourceMessage
    def __init__(self, object: _Optional[bytes] = ..., source: _Optional[_Union[ObjectSourceMessage, _Mapping]] = ...) -> None: ...

class CacheObjectRequest(_message.Message):
    __slots__ = ("container_name", "blob_name", "object", "cache_policy")
    CONTAINER_NAME_FIELD_NUMBER: _ClassVar[int]
    BLOB_NAME_FIELD_NUMBER: _ClassVar[int]
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    CACHE_POLICY_FIELD_NUMBER: _ClassVar[int]
    container_name: str
    blob_name: str
    object: bytes
    cache_policy: CacheObjectPolicy
    def __init__(self, container_name: _Optional[str] = ..., blob_name: _Optional[str] = ..., object: _Optional[bytes] = ..., cache_policy: _Optional[_Union[CacheObjectPolicy, str]] = ...) -> None: ...

class CacheObjectResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetCachedObjectRequest(_message.Message):
    __slots__ = ("container_name", "blob_name", "cache_policy")
    CONTAINER_NAME_FIELD_NUMBER: _ClassVar[int]
    BLOB_NAME_FIELD_NUMBER: _ClassVar[int]
    CACHE_POLICY_FIELD_NUMBER: _ClassVar[int]
    container_name: str
    blob_name: str
    cache_policy: CacheObjectPolicy
    def __init__(self, container_name: _Optional[str] = ..., blob_name: _Optional[str] = ..., cache_policy: _Optional[_Union[CacheObjectPolicy, str]] = ...) -> None: ...

class GetCachedObjectResponse(_message.Message):
    __slots__ = ("object",)
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    object: bytes
    def __init__(self, object: _Optional[bytes] = ...) -> None: ...

class HasObjectCachedRequest(_message.Message):
    __slots__ = ("container_name", "blob_name")
    CONTAINER_NAME_FIELD_NUMBER: _ClassVar[int]
    BLOB_NAME_FIELD_NUMBER: _ClassVar[int]
    container_name: str
    blob_name: str
    def __init__(self, container_name: _Optional[str] = ..., blob_name: _Optional[str] = ...) -> None: ...

class HasObjectCachedResponse(_message.Message):
    __slots__ = ("exists",)
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    exists: bool
    def __init__(self, exists: bool = ...) -> None: ...

class PingPongRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PingPongResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ChangeSettingsRequest(_message.Message):
    __slots__ = ("log_level",)
    LOG_LEVEL_FIELD_NUMBER: _ClassVar[int]
    log_level: str
    def __init__(self, log_level: _Optional[str] = ...) -> None: ...

class ChangeSettingsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InvalidateObjectRequest(_message.Message):
    __slots__ = ("container_name", "blob_name")
    CONTAINER_NAME_FIELD_NUMBER: _ClassVar[int]
    BLOB_NAME_FIELD_NUMBER: _ClassVar[int]
    container_name: str
    blob_name: str
    def __init__(self, container_name: _Optional[str] = ..., blob_name: _Optional[str] = ...) -> None: ...

class InvalidateObjectResponse(_message.Message):
    __slots__ = ("existed",)
    EXISTED_FIELD_NUMBER: _ClassVar[int]
    existed: bool
    def __init__(self, existed: bool = ...) -> None: ...
