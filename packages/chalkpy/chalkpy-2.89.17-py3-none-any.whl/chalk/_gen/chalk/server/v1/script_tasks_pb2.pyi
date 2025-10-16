from chalk._gen.chalk.auth.v1 import permissions_pb2 as _permissions_pb2
from chalk._gen.chalk.common.v1 import script_task_pb2 as _script_task_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class CreateScriptTaskRequest(_message.Message):
    __slots__ = ("request", "source_file")
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FILE_FIELD_NUMBER: _ClassVar[int]
    request: _script_task_pb2.ScriptTaskRequest
    source_file: bytes
    def __init__(
        self,
        request: _Optional[_Union[_script_task_pb2.ScriptTaskRequest, _Mapping]] = ...,
        source_file: _Optional[bytes] = ...,
    ) -> None: ...

class CreateScriptTaskResponse(_message.Message):
    __slots__ = ("task_id",)
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    def __init__(self, task_id: _Optional[str] = ...) -> None: ...

class ScriptTaskMeta(_message.Message):
    __slots__ = ("id", "operation_id", "status", "created_at", "completed_at", "branch_name", "raw_body_filename")
    ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_AT_FIELD_NUMBER: _ClassVar[int]
    BRANCH_NAME_FIELD_NUMBER: _ClassVar[int]
    RAW_BODY_FILENAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    operation_id: str
    status: _script_task_pb2.ScriptTaskStatus
    created_at: _timestamp_pb2.Timestamp
    completed_at: _timestamp_pb2.Timestamp
    branch_name: str
    raw_body_filename: str
    def __init__(
        self,
        id: _Optional[str] = ...,
        operation_id: _Optional[str] = ...,
        status: _Optional[_Union[_script_task_pb2.ScriptTaskStatus, str]] = ...,
        created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        completed_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        branch_name: _Optional[str] = ...,
        raw_body_filename: _Optional[str] = ...,
    ) -> None: ...

class ListScriptTasksRequest(_message.Message):
    __slots__ = ("limit", "cursor", "filters")
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    limit: int
    cursor: str
    filters: _containers.RepeatedCompositeFieldContainer[_script_task_pb2.ScriptTaskFilter]
    def __init__(
        self,
        limit: _Optional[int] = ...,
        cursor: _Optional[str] = ...,
        filters: _Optional[_Iterable[_Union[_script_task_pb2.ScriptTaskFilter, _Mapping]]] = ...,
    ) -> None: ...

class ListScriptTasksResponse(_message.Message):
    __slots__ = ("script_tasks", "next_cursor")
    SCRIPT_TASKS_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    script_tasks: _containers.RepeatedCompositeFieldContainer[ScriptTaskMeta]
    next_cursor: str
    def __init__(
        self,
        script_tasks: _Optional[_Iterable[_Union[ScriptTaskMeta, _Mapping]]] = ...,
        next_cursor: _Optional[str] = ...,
    ) -> None: ...

class GetScriptTaskRequest(_message.Message):
    __slots__ = ("script_task_id",)
    SCRIPT_TASK_ID_FIELD_NUMBER: _ClassVar[int]
    script_task_id: str
    def __init__(self, script_task_id: _Optional[str] = ...) -> None: ...

class GetScriptTaskResponse(_message.Message):
    __slots__ = ("script_task",)
    SCRIPT_TASK_FIELD_NUMBER: _ClassVar[int]
    script_task: ScriptTaskMeta
    def __init__(self, script_task: _Optional[_Union[ScriptTaskMeta, _Mapping]] = ...) -> None: ...
