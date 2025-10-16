from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StreamType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STREAM_TYPE_UNSPECIFIED: _ClassVar[StreamType]
    STREAM_TYPE_STDOUT: _ClassVar[StreamType]
    STREAM_TYPE_STDERR: _ClassVar[StreamType]
STREAM_TYPE_UNSPECIFIED: StreamType
STREAM_TYPE_STDOUT: StreamType
STREAM_TYPE_STDERR: StreamType

class QueryLogsRequest(_message.Message):
    __slots__ = ("job_id", "stream", "start_time", "end_time", "limit", "offset")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    STREAM_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    stream: StreamType
    start_time: int
    end_time: int
    limit: int
    offset: int
    def __init__(self, job_id: _Optional[str] = ..., stream: _Optional[_Union[StreamType, str]] = ..., start_time: _Optional[int] = ..., end_time: _Optional[int] = ..., limit: _Optional[int] = ..., offset: _Optional[int] = ...) -> None: ...

class QueryMetricsRequest(_message.Message):
    __slots__ = ("job_id", "start_time", "end_time", "limit", "offset")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    start_time: int
    end_time: int
    limit: int
    offset: int
    def __init__(self, job_id: _Optional[str] = ..., start_time: _Optional[int] = ..., end_time: _Optional[int] = ..., limit: _Optional[int] = ..., offset: _Optional[int] = ...) -> None: ...

class LogLine(_message.Message):
    __slots__ = ("job_id", "stream", "timestamp", "sequence", "content")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    STREAM_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    stream: StreamType
    timestamp: int
    sequence: int
    content: bytes
    def __init__(self, job_id: _Optional[str] = ..., stream: _Optional[_Union[StreamType, str]] = ..., timestamp: _Optional[int] = ..., sequence: _Optional[int] = ..., content: _Optional[bytes] = ...) -> None: ...

class Metric(_message.Message):
    __slots__ = ("job_id", "timestamp", "sequence", "data")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    timestamp: int
    sequence: int
    data: MetricData
    def __init__(self, job_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., sequence: _Optional[int] = ..., data: _Optional[_Union[MetricData, _Mapping]] = ...) -> None: ...

class MetricData(_message.Message):
    __slots__ = ("cpu_usage", "memory_usage", "gpu_usage", "disk_io", "network_io")
    CPU_USAGE_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USAGE_FIELD_NUMBER: _ClassVar[int]
    GPU_USAGE_FIELD_NUMBER: _ClassVar[int]
    DISK_IO_FIELD_NUMBER: _ClassVar[int]
    NETWORK_IO_FIELD_NUMBER: _ClassVar[int]
    cpu_usage: float
    memory_usage: int
    gpu_usage: float
    disk_io: DiskIO
    network_io: NetworkIO
    def __init__(self, cpu_usage: _Optional[float] = ..., memory_usage: _Optional[int] = ..., gpu_usage: _Optional[float] = ..., disk_io: _Optional[_Union[DiskIO, _Mapping]] = ..., network_io: _Optional[_Union[NetworkIO, _Mapping]] = ...) -> None: ...

class DiskIO(_message.Message):
    __slots__ = ("read_bytes", "write_bytes", "read_ops", "write_ops")
    READ_BYTES_FIELD_NUMBER: _ClassVar[int]
    WRITE_BYTES_FIELD_NUMBER: _ClassVar[int]
    READ_OPS_FIELD_NUMBER: _ClassVar[int]
    WRITE_OPS_FIELD_NUMBER: _ClassVar[int]
    read_bytes: int
    write_bytes: int
    read_ops: int
    write_ops: int
    def __init__(self, read_bytes: _Optional[int] = ..., write_bytes: _Optional[int] = ..., read_ops: _Optional[int] = ..., write_ops: _Optional[int] = ...) -> None: ...

class NetworkIO(_message.Message):
    __slots__ = ("rx_bytes", "tx_bytes", "rx_packets", "tx_packets")
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_PACKETS_FIELD_NUMBER: _ClassVar[int]
    TX_PACKETS_FIELD_NUMBER: _ClassVar[int]
    rx_bytes: int
    tx_bytes: int
    rx_packets: int
    tx_packets: int
    def __init__(self, rx_bytes: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_packets: _Optional[int] = ..., tx_packets: _Optional[int] = ...) -> None: ...

class DeleteJobRequest(_message.Message):
    __slots__ = ("job_id",)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...

class DeleteJobResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...
