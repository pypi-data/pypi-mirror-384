from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AcquireRequest(_message.Message):
    __slots__ = ("resource_name", "resource_key", "principal_id")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_KEY_FIELD_NUMBER: _ClassVar[int]
    PRINCIPAL_ID_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    resource_key: str
    principal_id: str
    def __init__(self, resource_name: _Optional[str] = ..., resource_key: _Optional[str] = ..., principal_id: _Optional[str] = ...) -> None: ...

class AcquireResponse(_message.Message):
    __slots__ = ("acquired_by", "acquired_by_name", "acquired_at", "retry_after")
    ACQUIRED_BY_FIELD_NUMBER: _ClassVar[int]
    ACQUIRED_BY_NAME_FIELD_NUMBER: _ClassVar[int]
    ACQUIRED_AT_FIELD_NUMBER: _ClassVar[int]
    RETRY_AFTER_FIELD_NUMBER: _ClassVar[int]
    acquired_by: str
    acquired_by_name: str
    acquired_at: str
    retry_after: int
    def __init__(self, acquired_by: _Optional[str] = ..., acquired_by_name: _Optional[str] = ..., acquired_at: _Optional[str] = ..., retry_after: _Optional[int] = ...) -> None: ...

class ReleaseRequest(_message.Message):
    __slots__ = ("id", "principal", "issued_at", "expires_at", "resource", "resource_key")
    ID_FIELD_NUMBER: _ClassVar[int]
    PRINCIPAL_FIELD_NUMBER: _ClassVar[int]
    ISSUED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_KEY_FIELD_NUMBER: _ClassVar[int]
    id: str
    principal: str
    issued_at: str
    expires_at: str
    resource: str
    resource_key: str
    def __init__(self, id: _Optional[str] = ..., principal: _Optional[str] = ..., issued_at: _Optional[str] = ..., expires_at: _Optional[str] = ..., resource: _Optional[str] = ..., resource_key: _Optional[str] = ...) -> None: ...

class ReleaseResponse(_message.Message):
    __slots__ = ("success", "error")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error: str
    def __init__(self, success: bool = ..., error: _Optional[str] = ...) -> None: ...
