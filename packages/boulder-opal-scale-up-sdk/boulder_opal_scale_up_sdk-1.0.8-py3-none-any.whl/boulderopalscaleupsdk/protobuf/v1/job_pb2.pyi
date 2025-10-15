from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetSummaryRequest(_message.Message):
    __slots__ = ("job_id",)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...

class GetSummaryResponse(_message.Message):
    __slots__ = ("job_summary_data",)
    JOB_SUMMARY_DATA_FIELD_NUMBER: _ClassVar[int]
    job_summary_data: _struct_pb2.Struct
    def __init__(self, job_summary_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class GetRequest(_message.Message):
    __slots__ = ("job_id",)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...

class GetResponse(_message.Message):
    __slots__ = ("job_data",)
    JOB_DATA_FIELD_NUMBER: _ClassVar[int]
    job_data: _struct_pb2.Struct
    def __init__(self, job_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class ListRequest(_message.Message):
    __slots__ = ("device_name", "job_name", "page", "limit", "sort_order")
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    JOB_NAME_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    job_name: str
    page: int
    limit: int
    sort_order: int
    def __init__(self, device_name: _Optional[str] = ..., job_name: _Optional[str] = ..., page: _Optional[int] = ..., limit: _Optional[int] = ..., sort_order: _Optional[int] = ...) -> None: ...

class ListResponse(_message.Message):
    __slots__ = ("jobs", "total_pages")
    JOBS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_PAGES_FIELD_NUMBER: _ClassVar[int]
    jobs: _containers.RepeatedCompositeFieldContainer[_struct_pb2.Struct]
    total_pages: int
    def __init__(self, jobs: _Optional[_Iterable[_Union[_struct_pb2.Struct, _Mapping]]] = ..., total_pages: _Optional[int] = ...) -> None: ...
