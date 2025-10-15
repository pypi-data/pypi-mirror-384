from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SelectionMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SELECTION_MODE_UNSPECIFIED: _ClassVar[SelectionMode]
    SELECTION_MODE_ITEMS: _ClassVar[SelectionMode]
    SELECTION_MODE_ALL: _ClassVar[SelectionMode]
SELECTION_MODE_UNSPECIFIED: SelectionMode
SELECTION_MODE_ITEMS: SelectionMode
SELECTION_MODE_ALL: SelectionMode

class SetSnapshotRequest(_message.Message):
    __slots__ = ("device_name", "data")
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    data: _struct_pb2.Struct
    def __init__(self, device_name: _Optional[str] = ..., data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class SetSnapshotResponse(_message.Message):
    __slots__ = ("device_name", "version")
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    version: int
    def __init__(self, device_name: _Optional[str] = ..., version: _Optional[int] = ...) -> None: ...

class GetSnapshotRequest(_message.Message):
    __slots__ = ("device_name", "version")
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    version: int
    def __init__(self, device_name: _Optional[str] = ..., version: _Optional[int] = ...) -> None: ...

class GetSnapshotResponse(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: _struct_pb2.Struct
    def __init__(self, data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class CreateRequest(_message.Message):
    __slots__ = ("app_name", "device_name", "device_data")
    APP_NAME_FIELD_NUMBER: _ClassVar[int]
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    DEVICE_DATA_FIELD_NUMBER: _ClassVar[int]
    app_name: str
    device_name: str
    device_data: _struct_pb2.Struct
    def __init__(self, app_name: _Optional[str] = ..., device_name: _Optional[str] = ..., device_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class CreateResponse(_message.Message):
    __slots__ = ("done",)
    DONE_FIELD_NUMBER: _ClassVar[int]
    done: bool
    def __init__(self, done: bool = ...) -> None: ...

class GetDataRequest(_message.Message):
    __slots__ = ("app_name", "device_name")
    APP_NAME_FIELD_NUMBER: _ClassVar[int]
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    app_name: str
    device_name: str
    def __init__(self, app_name: _Optional[str] = ..., device_name: _Optional[str] = ...) -> None: ...

class GetDataResponse(_message.Message):
    __slots__ = ("processor_data", "controller_data", "defcals")
    PROCESSOR_DATA_FIELD_NUMBER: _ClassVar[int]
    CONTROLLER_DATA_FIELD_NUMBER: _ClassVar[int]
    DEFCALS_FIELD_NUMBER: _ClassVar[int]
    processor_data: _struct_pb2.Struct
    controller_data: _struct_pb2.Struct
    defcals: _containers.RepeatedCompositeFieldContainer[_struct_pb2.Struct]
    def __init__(self, processor_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., controller_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., defcals: _Optional[_Iterable[_Union[_struct_pb2.Struct, _Mapping]]] = ...) -> None: ...

class UpdateRequest(_message.Message):
    __slots__ = ("app_name", "device_name", "processor_data")
    APP_NAME_FIELD_NUMBER: _ClassVar[int]
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    PROCESSOR_DATA_FIELD_NUMBER: _ClassVar[int]
    app_name: str
    device_name: str
    processor_data: _struct_pb2.Struct
    def __init__(self, app_name: _Optional[str] = ..., device_name: _Optional[str] = ..., processor_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class UpdateResponse(_message.Message):
    __slots__ = ("processor_data", "controller_data")
    PROCESSOR_DATA_FIELD_NUMBER: _ClassVar[int]
    CONTROLLER_DATA_FIELD_NUMBER: _ClassVar[int]
    processor_data: _struct_pb2.Struct
    controller_data: _struct_pb2.Struct
    def __init__(self, processor_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., controller_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class DeleteRequest(_message.Message):
    __slots__ = ("app_name", "device_name")
    APP_NAME_FIELD_NUMBER: _ClassVar[int]
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    app_name: str
    device_name: str
    def __init__(self, app_name: _Optional[str] = ..., device_name: _Optional[str] = ...) -> None: ...

class DeleteResponse(_message.Message):
    __slots__ = ("done",)
    DONE_FIELD_NUMBER: _ClassVar[int]
    done: bool
    def __init__(self, done: bool = ...) -> None: ...

class GetMetadataRequest(_message.Message):
    __slots__ = ("device_name",)
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    def __init__(self, device_name: _Optional[str] = ...) -> None: ...

class GetMetadataResponse(_message.Message):
    __slots__ = ("metadata",)
    METADATA_FIELD_NUMBER: _ClassVar[int]
    metadata: _struct_pb2.Struct
    def __init__(self, metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class GetAllDevicesMetadataRequest(_message.Message):
    __slots__ = ("limit", "next_cursor")
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    limit: int
    next_cursor: str
    def __init__(self, limit: _Optional[int] = ..., next_cursor: _Optional[str] = ...) -> None: ...

class GetAllDevicesMetadataResponse(_message.Message):
    __slots__ = ("metadatas", "next_cursor")
    METADATAS_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    metadatas: _containers.RepeatedCompositeFieldContainer[_struct_pb2.Struct]
    next_cursor: str
    def __init__(self, metadatas: _Optional[_Iterable[_Union[_struct_pb2.Struct, _Mapping]]] = ..., next_cursor: _Optional[str] = ...) -> None: ...

class MaskRequest(_message.Message):
    __slots__ = ("mode", "device_name", "elements")
    MODE_FIELD_NUMBER: _ClassVar[int]
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    mode: SelectionMode
    device_name: str
    elements: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, mode: _Optional[_Union[SelectionMode, str]] = ..., device_name: _Optional[str] = ..., elements: _Optional[_Iterable[str]] = ...) -> None: ...

class MaskResponse(_message.Message):
    __slots__ = ("done",)
    DONE_FIELD_NUMBER: _ClassVar[int]
    done: bool
    def __init__(self, done: bool = ...) -> None: ...

class UnmaskRequest(_message.Message):
    __slots__ = ("device_name", "elements")
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    elements: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, device_name: _Optional[str] = ..., elements: _Optional[_Iterable[str]] = ...) -> None: ...

class UnmaskResponse(_message.Message):
    __slots__ = ("done",)
    DONE_FIELD_NUMBER: _ClassVar[int]
    done: bool
    def __init__(self, done: bool = ...) -> None: ...
