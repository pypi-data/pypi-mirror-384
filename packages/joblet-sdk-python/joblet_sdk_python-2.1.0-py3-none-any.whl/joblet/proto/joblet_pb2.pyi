from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Jobs(_message.Message):
    __slots__ = ("jobs",)
    JOBS_FIELD_NUMBER: _ClassVar[int]
    jobs: _containers.RepeatedCompositeFieldContainer[Job]
    def __init__(self, jobs: _Optional[_Iterable[_Union[Job, _Mapping]]] = ...) -> None: ...

class Job(_message.Message):
    __slots__ = ("uuid", "name", "command", "args", "maxCPU", "cpuCores", "maxMemory", "maxIOBPS", "status", "startTime", "endTime", "exitCode", "scheduledTime", "runtime", "environment", "secret_environment", "gpu_indices", "gpu_count", "gpu_memory_mb", "nodeId")
    class EnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class SecretEnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    MAXCPU_FIELD_NUMBER: _ClassVar[int]
    CPUCORES_FIELD_NUMBER: _ClassVar[int]
    MAXMEMORY_FIELD_NUMBER: _ClassVar[int]
    MAXIOBPS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    SCHEDULEDTIME_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    SECRET_ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    GPU_INDICES_FIELD_NUMBER: _ClassVar[int]
    GPU_COUNT_FIELD_NUMBER: _ClassVar[int]
    GPU_MEMORY_MB_FIELD_NUMBER: _ClassVar[int]
    NODEID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    name: str
    command: str
    args: _containers.RepeatedScalarFieldContainer[str]
    maxCPU: int
    cpuCores: str
    maxMemory: int
    maxIOBPS: int
    status: str
    startTime: str
    endTime: str
    exitCode: int
    scheduledTime: str
    runtime: str
    environment: _containers.ScalarMap[str, str]
    secret_environment: _containers.ScalarMap[str, str]
    gpu_indices: _containers.RepeatedScalarFieldContainer[int]
    gpu_count: int
    gpu_memory_mb: int
    nodeId: str
    def __init__(self, uuid: _Optional[str] = ..., name: _Optional[str] = ..., command: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ..., maxCPU: _Optional[int] = ..., cpuCores: _Optional[str] = ..., maxMemory: _Optional[int] = ..., maxIOBPS: _Optional[int] = ..., status: _Optional[str] = ..., startTime: _Optional[str] = ..., endTime: _Optional[str] = ..., exitCode: _Optional[int] = ..., scheduledTime: _Optional[str] = ..., runtime: _Optional[str] = ..., environment: _Optional[_Mapping[str, str]] = ..., secret_environment: _Optional[_Mapping[str, str]] = ..., gpu_indices: _Optional[_Iterable[int]] = ..., gpu_count: _Optional[int] = ..., gpu_memory_mb: _Optional[int] = ..., nodeId: _Optional[str] = ...) -> None: ...

class EmptyRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FileUpload(_message.Message):
    __slots__ = ("path", "content", "mode", "isDirectory")
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    ISDIRECTORY_FIELD_NUMBER: _ClassVar[int]
    path: str
    content: bytes
    mode: int
    isDirectory: bool
    def __init__(self, path: _Optional[str] = ..., content: _Optional[bytes] = ..., mode: _Optional[int] = ..., isDirectory: bool = ...) -> None: ...

class GetJobStatusReq(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class GetJobStatusRes(_message.Message):
    __slots__ = ("uuid", "name", "command", "args", "maxCPU", "cpuCores", "maxMemory", "maxIOBPS", "status", "startTime", "endTime", "exitCode", "scheduledTime", "environment", "secret_environment", "network", "volumes", "runtime", "workDir", "uploads", "dependencies", "workflowUuid", "gpu_indices", "gpu_count", "gpu_memory_mb", "nodeId")
    class EnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class SecretEnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    MAXCPU_FIELD_NUMBER: _ClassVar[int]
    CPUCORES_FIELD_NUMBER: _ClassVar[int]
    MAXMEMORY_FIELD_NUMBER: _ClassVar[int]
    MAXIOBPS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    SCHEDULEDTIME_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    SECRET_ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    VOLUMES_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    WORKDIR_FIELD_NUMBER: _ClassVar[int]
    UPLOADS_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCIES_FIELD_NUMBER: _ClassVar[int]
    WORKFLOWUUID_FIELD_NUMBER: _ClassVar[int]
    GPU_INDICES_FIELD_NUMBER: _ClassVar[int]
    GPU_COUNT_FIELD_NUMBER: _ClassVar[int]
    GPU_MEMORY_MB_FIELD_NUMBER: _ClassVar[int]
    NODEID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    name: str
    command: str
    args: _containers.RepeatedScalarFieldContainer[str]
    maxCPU: int
    cpuCores: str
    maxMemory: int
    maxIOBPS: int
    status: str
    startTime: str
    endTime: str
    exitCode: int
    scheduledTime: str
    environment: _containers.ScalarMap[str, str]
    secret_environment: _containers.ScalarMap[str, str]
    network: str
    volumes: _containers.RepeatedScalarFieldContainer[str]
    runtime: str
    workDir: str
    uploads: _containers.RepeatedScalarFieldContainer[str]
    dependencies: _containers.RepeatedScalarFieldContainer[str]
    workflowUuid: str
    gpu_indices: _containers.RepeatedScalarFieldContainer[int]
    gpu_count: int
    gpu_memory_mb: int
    nodeId: str
    def __init__(self, uuid: _Optional[str] = ..., name: _Optional[str] = ..., command: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ..., maxCPU: _Optional[int] = ..., cpuCores: _Optional[str] = ..., maxMemory: _Optional[int] = ..., maxIOBPS: _Optional[int] = ..., status: _Optional[str] = ..., startTime: _Optional[str] = ..., endTime: _Optional[str] = ..., exitCode: _Optional[int] = ..., scheduledTime: _Optional[str] = ..., environment: _Optional[_Mapping[str, str]] = ..., secret_environment: _Optional[_Mapping[str, str]] = ..., network: _Optional[str] = ..., volumes: _Optional[_Iterable[str]] = ..., runtime: _Optional[str] = ..., workDir: _Optional[str] = ..., uploads: _Optional[_Iterable[str]] = ..., dependencies: _Optional[_Iterable[str]] = ..., workflowUuid: _Optional[str] = ..., gpu_indices: _Optional[_Iterable[int]] = ..., gpu_count: _Optional[int] = ..., gpu_memory_mb: _Optional[int] = ..., nodeId: _Optional[str] = ...) -> None: ...

class StopJobReq(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class StopJobRes(_message.Message):
    __slots__ = ("uuid", "status", "endTime", "exitCode")
    UUID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    status: str
    endTime: str
    exitCode: int
    def __init__(self, uuid: _Optional[str] = ..., status: _Optional[str] = ..., endTime: _Optional[str] = ..., exitCode: _Optional[int] = ...) -> None: ...

class CancelJobReq(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class CancelJobRes(_message.Message):
    __slots__ = ("uuid", "status")
    UUID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    status: str
    def __init__(self, uuid: _Optional[str] = ..., status: _Optional[str] = ...) -> None: ...

class DeleteJobReq(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class DeleteJobRes(_message.Message):
    __slots__ = ("uuid", "success", "message")
    UUID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    success: bool
    message: str
    def __init__(self, uuid: _Optional[str] = ..., success: bool = ..., message: _Optional[str] = ...) -> None: ...

class DeleteAllJobsReq(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DeleteAllJobsRes(_message.Message):
    __slots__ = ("success", "message", "deleted_count", "skipped_count")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DELETED_COUNT_FIELD_NUMBER: _ClassVar[int]
    SKIPPED_COUNT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    deleted_count: int
    skipped_count: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., deleted_count: _Optional[int] = ..., skipped_count: _Optional[int] = ...) -> None: ...

class GetJobLogsReq(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class DataChunk(_message.Message):
    __slots__ = ("payload",)
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: bytes
    def __init__(self, payload: _Optional[bytes] = ...) -> None: ...

class RuntimeInstallationChunk(_message.Message):
    __slots__ = ("progress", "log", "result")
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    LOG_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    progress: RuntimeInstallationProgress
    log: RuntimeInstallationLog
    result: RuntimeInstallationResult
    def __init__(self, progress: _Optional[_Union[RuntimeInstallationProgress, _Mapping]] = ..., log: _Optional[_Union[RuntimeInstallationLog, _Mapping]] = ..., result: _Optional[_Union[RuntimeInstallationResult, _Mapping]] = ...) -> None: ...

class RuntimeInstallationProgress(_message.Message):
    __slots__ = ("message", "step", "total_steps")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STEP_FIELD_NUMBER: _ClassVar[int]
    TOTAL_STEPS_FIELD_NUMBER: _ClassVar[int]
    message: str
    step: int
    total_steps: int
    def __init__(self, message: _Optional[str] = ..., step: _Optional[int] = ..., total_steps: _Optional[int] = ...) -> None: ...

class RuntimeInstallationLog(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    def __init__(self, data: _Optional[bytes] = ...) -> None: ...

class RuntimeInstallationResult(_message.Message):
    __slots__ = ("success", "message", "runtime_spec", "install_path")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_SPEC_FIELD_NUMBER: _ClassVar[int]
    INSTALL_PATH_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    runtime_spec: str
    install_path: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., runtime_spec: _Optional[str] = ..., install_path: _Optional[str] = ...) -> None: ...

class CreateNetworkReq(_message.Message):
    __slots__ = ("name", "cidr")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CIDR_FIELD_NUMBER: _ClassVar[int]
    name: str
    cidr: str
    def __init__(self, name: _Optional[str] = ..., cidr: _Optional[str] = ...) -> None: ...

class CreateNetworkRes(_message.Message):
    __slots__ = ("name", "cidr", "bridge")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CIDR_FIELD_NUMBER: _ClassVar[int]
    BRIDGE_FIELD_NUMBER: _ClassVar[int]
    name: str
    cidr: str
    bridge: str
    def __init__(self, name: _Optional[str] = ..., cidr: _Optional[str] = ..., bridge: _Optional[str] = ...) -> None: ...

class RemoveNetworkReq(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class RemoveNetworkRes(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class Network(_message.Message):
    __slots__ = ("name", "cidr", "bridge", "jobCount")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CIDR_FIELD_NUMBER: _ClassVar[int]
    BRIDGE_FIELD_NUMBER: _ClassVar[int]
    JOBCOUNT_FIELD_NUMBER: _ClassVar[int]
    name: str
    cidr: str
    bridge: str
    jobCount: int
    def __init__(self, name: _Optional[str] = ..., cidr: _Optional[str] = ..., bridge: _Optional[str] = ..., jobCount: _Optional[int] = ...) -> None: ...

class Networks(_message.Message):
    __slots__ = ("networks",)
    NETWORKS_FIELD_NUMBER: _ClassVar[int]
    networks: _containers.RepeatedCompositeFieldContainer[Network]
    def __init__(self, networks: _Optional[_Iterable[_Union[Network, _Mapping]]] = ...) -> None: ...

class CreateVolumeReq(_message.Message):
    __slots__ = ("name", "size", "type")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    size: str
    type: str
    def __init__(self, name: _Optional[str] = ..., size: _Optional[str] = ..., type: _Optional[str] = ...) -> None: ...

class CreateVolumeRes(_message.Message):
    __slots__ = ("name", "size", "type", "path")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    name: str
    size: str
    type: str
    path: str
    def __init__(self, name: _Optional[str] = ..., size: _Optional[str] = ..., type: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class RemoveVolumeReq(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class RemoveVolumeRes(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class Volume(_message.Message):
    __slots__ = ("name", "size", "type", "path", "createdTime", "jobCount")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    CREATEDTIME_FIELD_NUMBER: _ClassVar[int]
    JOBCOUNT_FIELD_NUMBER: _ClassVar[int]
    name: str
    size: str
    type: str
    path: str
    createdTime: str
    jobCount: int
    def __init__(self, name: _Optional[str] = ..., size: _Optional[str] = ..., type: _Optional[str] = ..., path: _Optional[str] = ..., createdTime: _Optional[str] = ..., jobCount: _Optional[int] = ...) -> None: ...

class Volumes(_message.Message):
    __slots__ = ("volumes",)
    VOLUMES_FIELD_NUMBER: _ClassVar[int]
    volumes: _containers.RepeatedCompositeFieldContainer[Volume]
    def __init__(self, volumes: _Optional[_Iterable[_Union[Volume, _Mapping]]] = ...) -> None: ...

class SystemStatusRes(_message.Message):
    __slots__ = ("timestamp", "available", "host", "cpu", "memory", "disks", "networks", "io", "processes", "cloud", "server_version")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    CPU_FIELD_NUMBER: _ClassVar[int]
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    DISKS_FIELD_NUMBER: _ClassVar[int]
    NETWORKS_FIELD_NUMBER: _ClassVar[int]
    IO_FIELD_NUMBER: _ClassVar[int]
    PROCESSES_FIELD_NUMBER: _ClassVar[int]
    CLOUD_FIELD_NUMBER: _ClassVar[int]
    SERVER_VERSION_FIELD_NUMBER: _ClassVar[int]
    timestamp: str
    available: bool
    host: HostInfo
    cpu: CPUMetrics
    memory: MemoryMetrics
    disks: _containers.RepeatedCompositeFieldContainer[DiskMetrics]
    networks: _containers.RepeatedCompositeFieldContainer[NetworkMetrics]
    io: IOMetrics
    processes: ProcessMetrics
    cloud: CloudInfo
    server_version: ServerVersionInfo
    def __init__(self, timestamp: _Optional[str] = ..., available: bool = ..., host: _Optional[_Union[HostInfo, _Mapping]] = ..., cpu: _Optional[_Union[CPUMetrics, _Mapping]] = ..., memory: _Optional[_Union[MemoryMetrics, _Mapping]] = ..., disks: _Optional[_Iterable[_Union[DiskMetrics, _Mapping]]] = ..., networks: _Optional[_Iterable[_Union[NetworkMetrics, _Mapping]]] = ..., io: _Optional[_Union[IOMetrics, _Mapping]] = ..., processes: _Optional[_Union[ProcessMetrics, _Mapping]] = ..., cloud: _Optional[_Union[CloudInfo, _Mapping]] = ..., server_version: _Optional[_Union[ServerVersionInfo, _Mapping]] = ...) -> None: ...

class SystemMetricsRes(_message.Message):
    __slots__ = ("timestamp", "host", "cpu", "memory", "disks", "networks", "io", "processes", "cloud")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    CPU_FIELD_NUMBER: _ClassVar[int]
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    DISKS_FIELD_NUMBER: _ClassVar[int]
    NETWORKS_FIELD_NUMBER: _ClassVar[int]
    IO_FIELD_NUMBER: _ClassVar[int]
    PROCESSES_FIELD_NUMBER: _ClassVar[int]
    CLOUD_FIELD_NUMBER: _ClassVar[int]
    timestamp: str
    host: HostInfo
    cpu: CPUMetrics
    memory: MemoryMetrics
    disks: _containers.RepeatedCompositeFieldContainer[DiskMetrics]
    networks: _containers.RepeatedCompositeFieldContainer[NetworkMetrics]
    io: IOMetrics
    processes: ProcessMetrics
    cloud: CloudInfo
    def __init__(self, timestamp: _Optional[str] = ..., host: _Optional[_Union[HostInfo, _Mapping]] = ..., cpu: _Optional[_Union[CPUMetrics, _Mapping]] = ..., memory: _Optional[_Union[MemoryMetrics, _Mapping]] = ..., disks: _Optional[_Iterable[_Union[DiskMetrics, _Mapping]]] = ..., networks: _Optional[_Iterable[_Union[NetworkMetrics, _Mapping]]] = ..., io: _Optional[_Union[IOMetrics, _Mapping]] = ..., processes: _Optional[_Union[ProcessMetrics, _Mapping]] = ..., cloud: _Optional[_Union[CloudInfo, _Mapping]] = ...) -> None: ...

class StreamMetricsReq(_message.Message):
    __slots__ = ("intervalSeconds", "metricTypes")
    INTERVALSECONDS_FIELD_NUMBER: _ClassVar[int]
    METRICTYPES_FIELD_NUMBER: _ClassVar[int]
    intervalSeconds: int
    metricTypes: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, intervalSeconds: _Optional[int] = ..., metricTypes: _Optional[_Iterable[str]] = ...) -> None: ...

class HostInfo(_message.Message):
    __slots__ = ("hostname", "os", "platform", "platformFamily", "platformVersion", "kernelVersion", "kernelArch", "architecture", "cpuCount", "totalMemory", "bootTime", "uptime", "nodeId", "serverIPs", "macAddresses")
    HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    OS_FIELD_NUMBER: _ClassVar[int]
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    PLATFORMFAMILY_FIELD_NUMBER: _ClassVar[int]
    PLATFORMVERSION_FIELD_NUMBER: _ClassVar[int]
    KERNELVERSION_FIELD_NUMBER: _ClassVar[int]
    KERNELARCH_FIELD_NUMBER: _ClassVar[int]
    ARCHITECTURE_FIELD_NUMBER: _ClassVar[int]
    CPUCOUNT_FIELD_NUMBER: _ClassVar[int]
    TOTALMEMORY_FIELD_NUMBER: _ClassVar[int]
    BOOTTIME_FIELD_NUMBER: _ClassVar[int]
    UPTIME_FIELD_NUMBER: _ClassVar[int]
    NODEID_FIELD_NUMBER: _ClassVar[int]
    SERVERIPS_FIELD_NUMBER: _ClassVar[int]
    MACADDRESSES_FIELD_NUMBER: _ClassVar[int]
    hostname: str
    os: str
    platform: str
    platformFamily: str
    platformVersion: str
    kernelVersion: str
    kernelArch: str
    architecture: str
    cpuCount: int
    totalMemory: int
    bootTime: str
    uptime: int
    nodeId: str
    serverIPs: _containers.RepeatedScalarFieldContainer[str]
    macAddresses: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, hostname: _Optional[str] = ..., os: _Optional[str] = ..., platform: _Optional[str] = ..., platformFamily: _Optional[str] = ..., platformVersion: _Optional[str] = ..., kernelVersion: _Optional[str] = ..., kernelArch: _Optional[str] = ..., architecture: _Optional[str] = ..., cpuCount: _Optional[int] = ..., totalMemory: _Optional[int] = ..., bootTime: _Optional[str] = ..., uptime: _Optional[int] = ..., nodeId: _Optional[str] = ..., serverIPs: _Optional[_Iterable[str]] = ..., macAddresses: _Optional[_Iterable[str]] = ...) -> None: ...

class CPUMetrics(_message.Message):
    __slots__ = ("cores", "usagePercent", "userTime", "systemTime", "idleTime", "ioWaitTime", "stealTime", "loadAverage", "perCoreUsage")
    CORES_FIELD_NUMBER: _ClassVar[int]
    USAGEPERCENT_FIELD_NUMBER: _ClassVar[int]
    USERTIME_FIELD_NUMBER: _ClassVar[int]
    SYSTEMTIME_FIELD_NUMBER: _ClassVar[int]
    IDLETIME_FIELD_NUMBER: _ClassVar[int]
    IOWAITTIME_FIELD_NUMBER: _ClassVar[int]
    STEALTIME_FIELD_NUMBER: _ClassVar[int]
    LOADAVERAGE_FIELD_NUMBER: _ClassVar[int]
    PERCOREUSAGE_FIELD_NUMBER: _ClassVar[int]
    cores: int
    usagePercent: float
    userTime: float
    systemTime: float
    idleTime: float
    ioWaitTime: float
    stealTime: float
    loadAverage: _containers.RepeatedScalarFieldContainer[float]
    perCoreUsage: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, cores: _Optional[int] = ..., usagePercent: _Optional[float] = ..., userTime: _Optional[float] = ..., systemTime: _Optional[float] = ..., idleTime: _Optional[float] = ..., ioWaitTime: _Optional[float] = ..., stealTime: _Optional[float] = ..., loadAverage: _Optional[_Iterable[float]] = ..., perCoreUsage: _Optional[_Iterable[float]] = ...) -> None: ...

class MemoryMetrics(_message.Message):
    __slots__ = ("totalBytes", "usedBytes", "freeBytes", "availableBytes", "usagePercent", "cachedBytes", "bufferedBytes", "swapTotal", "swapUsed", "swapFree")
    TOTALBYTES_FIELD_NUMBER: _ClassVar[int]
    USEDBYTES_FIELD_NUMBER: _ClassVar[int]
    FREEBYTES_FIELD_NUMBER: _ClassVar[int]
    AVAILABLEBYTES_FIELD_NUMBER: _ClassVar[int]
    USAGEPERCENT_FIELD_NUMBER: _ClassVar[int]
    CACHEDBYTES_FIELD_NUMBER: _ClassVar[int]
    BUFFEREDBYTES_FIELD_NUMBER: _ClassVar[int]
    SWAPTOTAL_FIELD_NUMBER: _ClassVar[int]
    SWAPUSED_FIELD_NUMBER: _ClassVar[int]
    SWAPFREE_FIELD_NUMBER: _ClassVar[int]
    totalBytes: int
    usedBytes: int
    freeBytes: int
    availableBytes: int
    usagePercent: float
    cachedBytes: int
    bufferedBytes: int
    swapTotal: int
    swapUsed: int
    swapFree: int
    def __init__(self, totalBytes: _Optional[int] = ..., usedBytes: _Optional[int] = ..., freeBytes: _Optional[int] = ..., availableBytes: _Optional[int] = ..., usagePercent: _Optional[float] = ..., cachedBytes: _Optional[int] = ..., bufferedBytes: _Optional[int] = ..., swapTotal: _Optional[int] = ..., swapUsed: _Optional[int] = ..., swapFree: _Optional[int] = ...) -> None: ...

class DiskMetrics(_message.Message):
    __slots__ = ("device", "mountPoint", "filesystem", "totalBytes", "usedBytes", "freeBytes", "usagePercent", "inodesTotal", "inodesUsed", "inodesFree", "inodesUsagePercent")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    MOUNTPOINT_FIELD_NUMBER: _ClassVar[int]
    FILESYSTEM_FIELD_NUMBER: _ClassVar[int]
    TOTALBYTES_FIELD_NUMBER: _ClassVar[int]
    USEDBYTES_FIELD_NUMBER: _ClassVar[int]
    FREEBYTES_FIELD_NUMBER: _ClassVar[int]
    USAGEPERCENT_FIELD_NUMBER: _ClassVar[int]
    INODESTOTAL_FIELD_NUMBER: _ClassVar[int]
    INODESUSED_FIELD_NUMBER: _ClassVar[int]
    INODESFREE_FIELD_NUMBER: _ClassVar[int]
    INODESUSAGEPERCENT_FIELD_NUMBER: _ClassVar[int]
    device: str
    mountPoint: str
    filesystem: str
    totalBytes: int
    usedBytes: int
    freeBytes: int
    usagePercent: float
    inodesTotal: int
    inodesUsed: int
    inodesFree: int
    inodesUsagePercent: float
    def __init__(self, device: _Optional[str] = ..., mountPoint: _Optional[str] = ..., filesystem: _Optional[str] = ..., totalBytes: _Optional[int] = ..., usedBytes: _Optional[int] = ..., freeBytes: _Optional[int] = ..., usagePercent: _Optional[float] = ..., inodesTotal: _Optional[int] = ..., inodesUsed: _Optional[int] = ..., inodesFree: _Optional[int] = ..., inodesUsagePercent: _Optional[float] = ...) -> None: ...

class NetworkMetrics(_message.Message):
    __slots__ = ("interface", "bytesReceived", "bytesSent", "packetsReceived", "packetsSent", "errorsIn", "errorsOut", "dropsIn", "dropsOut", "receiveRate", "transmitRate", "ipAddresses", "macAddress")
    INTERFACE_FIELD_NUMBER: _ClassVar[int]
    BYTESRECEIVED_FIELD_NUMBER: _ClassVar[int]
    BYTESSENT_FIELD_NUMBER: _ClassVar[int]
    PACKETSRECEIVED_FIELD_NUMBER: _ClassVar[int]
    PACKETSSENT_FIELD_NUMBER: _ClassVar[int]
    ERRORSIN_FIELD_NUMBER: _ClassVar[int]
    ERRORSOUT_FIELD_NUMBER: _ClassVar[int]
    DROPSIN_FIELD_NUMBER: _ClassVar[int]
    DROPSOUT_FIELD_NUMBER: _ClassVar[int]
    RECEIVERATE_FIELD_NUMBER: _ClassVar[int]
    TRANSMITRATE_FIELD_NUMBER: _ClassVar[int]
    IPADDRESSES_FIELD_NUMBER: _ClassVar[int]
    MACADDRESS_FIELD_NUMBER: _ClassVar[int]
    interface: str
    bytesReceived: int
    bytesSent: int
    packetsReceived: int
    packetsSent: int
    errorsIn: int
    errorsOut: int
    dropsIn: int
    dropsOut: int
    receiveRate: float
    transmitRate: float
    ipAddresses: _containers.RepeatedScalarFieldContainer[str]
    macAddress: str
    def __init__(self, interface: _Optional[str] = ..., bytesReceived: _Optional[int] = ..., bytesSent: _Optional[int] = ..., packetsReceived: _Optional[int] = ..., packetsSent: _Optional[int] = ..., errorsIn: _Optional[int] = ..., errorsOut: _Optional[int] = ..., dropsIn: _Optional[int] = ..., dropsOut: _Optional[int] = ..., receiveRate: _Optional[float] = ..., transmitRate: _Optional[float] = ..., ipAddresses: _Optional[_Iterable[str]] = ..., macAddress: _Optional[str] = ...) -> None: ...

class IOMetrics(_message.Message):
    __slots__ = ("totalReads", "totalWrites", "readBytes", "writeBytes", "readRate", "writeRate", "diskIO")
    TOTALREADS_FIELD_NUMBER: _ClassVar[int]
    TOTALWRITES_FIELD_NUMBER: _ClassVar[int]
    READBYTES_FIELD_NUMBER: _ClassVar[int]
    WRITEBYTES_FIELD_NUMBER: _ClassVar[int]
    READRATE_FIELD_NUMBER: _ClassVar[int]
    WRITERATE_FIELD_NUMBER: _ClassVar[int]
    DISKIO_FIELD_NUMBER: _ClassVar[int]
    totalReads: int
    totalWrites: int
    readBytes: int
    writeBytes: int
    readRate: float
    writeRate: float
    diskIO: _containers.RepeatedCompositeFieldContainer[DiskIOMetrics]
    def __init__(self, totalReads: _Optional[int] = ..., totalWrites: _Optional[int] = ..., readBytes: _Optional[int] = ..., writeBytes: _Optional[int] = ..., readRate: _Optional[float] = ..., writeRate: _Optional[float] = ..., diskIO: _Optional[_Iterable[_Union[DiskIOMetrics, _Mapping]]] = ...) -> None: ...

class DiskIOMetrics(_message.Message):
    __slots__ = ("device", "readsCompleted", "writesCompleted", "readBytes", "writeBytes", "readTime", "writeTime", "ioTime", "utilization")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    READSCOMPLETED_FIELD_NUMBER: _ClassVar[int]
    WRITESCOMPLETED_FIELD_NUMBER: _ClassVar[int]
    READBYTES_FIELD_NUMBER: _ClassVar[int]
    WRITEBYTES_FIELD_NUMBER: _ClassVar[int]
    READTIME_FIELD_NUMBER: _ClassVar[int]
    WRITETIME_FIELD_NUMBER: _ClassVar[int]
    IOTIME_FIELD_NUMBER: _ClassVar[int]
    UTILIZATION_FIELD_NUMBER: _ClassVar[int]
    device: str
    readsCompleted: int
    writesCompleted: int
    readBytes: int
    writeBytes: int
    readTime: int
    writeTime: int
    ioTime: int
    utilization: float
    def __init__(self, device: _Optional[str] = ..., readsCompleted: _Optional[int] = ..., writesCompleted: _Optional[int] = ..., readBytes: _Optional[int] = ..., writeBytes: _Optional[int] = ..., readTime: _Optional[int] = ..., writeTime: _Optional[int] = ..., ioTime: _Optional[int] = ..., utilization: _Optional[float] = ...) -> None: ...

class ProcessMetrics(_message.Message):
    __slots__ = ("totalProcesses", "runningProcesses", "sleepingProcesses", "stoppedProcesses", "zombieProcesses", "totalThreads", "topByCPU", "topByMemory")
    TOTALPROCESSES_FIELD_NUMBER: _ClassVar[int]
    RUNNINGPROCESSES_FIELD_NUMBER: _ClassVar[int]
    SLEEPINGPROCESSES_FIELD_NUMBER: _ClassVar[int]
    STOPPEDPROCESSES_FIELD_NUMBER: _ClassVar[int]
    ZOMBIEPROCESSES_FIELD_NUMBER: _ClassVar[int]
    TOTALTHREADS_FIELD_NUMBER: _ClassVar[int]
    TOPBYCPU_FIELD_NUMBER: _ClassVar[int]
    TOPBYMEMORY_FIELD_NUMBER: _ClassVar[int]
    totalProcesses: int
    runningProcesses: int
    sleepingProcesses: int
    stoppedProcesses: int
    zombieProcesses: int
    totalThreads: int
    topByCPU: _containers.RepeatedCompositeFieldContainer[ProcessInfo]
    topByMemory: _containers.RepeatedCompositeFieldContainer[ProcessInfo]
    def __init__(self, totalProcesses: _Optional[int] = ..., runningProcesses: _Optional[int] = ..., sleepingProcesses: _Optional[int] = ..., stoppedProcesses: _Optional[int] = ..., zombieProcesses: _Optional[int] = ..., totalThreads: _Optional[int] = ..., topByCPU: _Optional[_Iterable[_Union[ProcessInfo, _Mapping]]] = ..., topByMemory: _Optional[_Iterable[_Union[ProcessInfo, _Mapping]]] = ...) -> None: ...

class ProcessInfo(_message.Message):
    __slots__ = ("pid", "ppid", "name", "command", "cpuPercent", "memoryPercent", "memoryBytes", "status", "startTime", "user")
    PID_FIELD_NUMBER: _ClassVar[int]
    PPID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    CPUPERCENT_FIELD_NUMBER: _ClassVar[int]
    MEMORYPERCENT_FIELD_NUMBER: _ClassVar[int]
    MEMORYBYTES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    pid: int
    ppid: int
    name: str
    command: str
    cpuPercent: float
    memoryPercent: float
    memoryBytes: int
    status: str
    startTime: str
    user: str
    def __init__(self, pid: _Optional[int] = ..., ppid: _Optional[int] = ..., name: _Optional[str] = ..., command: _Optional[str] = ..., cpuPercent: _Optional[float] = ..., memoryPercent: _Optional[float] = ..., memoryBytes: _Optional[int] = ..., status: _Optional[str] = ..., startTime: _Optional[str] = ..., user: _Optional[str] = ...) -> None: ...

class CloudInfo(_message.Message):
    __slots__ = ("provider", "region", "zone", "instanceID", "instanceType", "hypervisorType", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PROVIDER_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    ZONE_FIELD_NUMBER: _ClassVar[int]
    INSTANCEID_FIELD_NUMBER: _ClassVar[int]
    INSTANCETYPE_FIELD_NUMBER: _ClassVar[int]
    HYPERVISORTYPE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    provider: str
    region: str
    zone: str
    instanceID: str
    instanceType: str
    hypervisorType: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, provider: _Optional[str] = ..., region: _Optional[str] = ..., zone: _Optional[str] = ..., instanceID: _Optional[str] = ..., instanceType: _Optional[str] = ..., hypervisorType: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ServerVersionInfo(_message.Message):
    __slots__ = ("version", "git_commit", "git_tag", "build_date", "component", "go_version", "platform", "proto_commit", "proto_tag")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    GIT_COMMIT_FIELD_NUMBER: _ClassVar[int]
    GIT_TAG_FIELD_NUMBER: _ClassVar[int]
    BUILD_DATE_FIELD_NUMBER: _ClassVar[int]
    COMPONENT_FIELD_NUMBER: _ClassVar[int]
    GO_VERSION_FIELD_NUMBER: _ClassVar[int]
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    PROTO_COMMIT_FIELD_NUMBER: _ClassVar[int]
    PROTO_TAG_FIELD_NUMBER: _ClassVar[int]
    version: str
    git_commit: str
    git_tag: str
    build_date: str
    component: str
    go_version: str
    platform: str
    proto_commit: str
    proto_tag: str
    def __init__(self, version: _Optional[str] = ..., git_commit: _Optional[str] = ..., git_tag: _Optional[str] = ..., build_date: _Optional[str] = ..., component: _Optional[str] = ..., go_version: _Optional[str] = ..., platform: _Optional[str] = ..., proto_commit: _Optional[str] = ..., proto_tag: _Optional[str] = ...) -> None: ...

class RuntimesRes(_message.Message):
    __slots__ = ("runtimes",)
    RUNTIMES_FIELD_NUMBER: _ClassVar[int]
    runtimes: _containers.RepeatedCompositeFieldContainer[RuntimeInfo]
    def __init__(self, runtimes: _Optional[_Iterable[_Union[RuntimeInfo, _Mapping]]] = ...) -> None: ...

class RuntimeInfo(_message.Message):
    __slots__ = ("name", "language", "version", "description", "sizeBytes", "packages", "available", "requirements")
    NAME_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SIZEBYTES_FIELD_NUMBER: _ClassVar[int]
    PACKAGES_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    REQUIREMENTS_FIELD_NUMBER: _ClassVar[int]
    name: str
    language: str
    version: str
    description: str
    sizeBytes: int
    packages: _containers.RepeatedScalarFieldContainer[str]
    available: bool
    requirements: RuntimeRequirements
    def __init__(self, name: _Optional[str] = ..., language: _Optional[str] = ..., version: _Optional[str] = ..., description: _Optional[str] = ..., sizeBytes: _Optional[int] = ..., packages: _Optional[_Iterable[str]] = ..., available: bool = ..., requirements: _Optional[_Union[RuntimeRequirements, _Mapping]] = ...) -> None: ...

class RuntimeRequirements(_message.Message):
    __slots__ = ("architectures", "gpu")
    ARCHITECTURES_FIELD_NUMBER: _ClassVar[int]
    GPU_FIELD_NUMBER: _ClassVar[int]
    architectures: _containers.RepeatedScalarFieldContainer[str]
    gpu: bool
    def __init__(self, architectures: _Optional[_Iterable[str]] = ..., gpu: bool = ...) -> None: ...

class RuntimeInfoReq(_message.Message):
    __slots__ = ("runtime",)
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    runtime: str
    def __init__(self, runtime: _Optional[str] = ...) -> None: ...

class RuntimeInfoRes(_message.Message):
    __slots__ = ("runtime", "found")
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    FOUND_FIELD_NUMBER: _ClassVar[int]
    runtime: RuntimeInfo
    found: bool
    def __init__(self, runtime: _Optional[_Union[RuntimeInfo, _Mapping]] = ..., found: bool = ...) -> None: ...

class RuntimeTestReq(_message.Message):
    __slots__ = ("runtime",)
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    runtime: str
    def __init__(self, runtime: _Optional[str] = ...) -> None: ...

class RuntimeTestRes(_message.Message):
    __slots__ = ("success", "output", "error", "exitCode")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    output: str
    error: str
    exitCode: int
    def __init__(self, success: bool = ..., output: _Optional[str] = ..., error: _Optional[str] = ..., exitCode: _Optional[int] = ...) -> None: ...

class RunJobRequest(_message.Message):
    __slots__ = ("name", "command", "args", "maxCpu", "cpuCores", "maxMemory", "maxIobps", "uploads", "schedule", "network", "volumes", "runtime", "workDir", "environment", "secret_environment", "workflowUuid", "jobUuid", "requirements", "gpu_count", "gpu_memory_mb")
    class EnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class SecretEnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    MAXCPU_FIELD_NUMBER: _ClassVar[int]
    CPUCORES_FIELD_NUMBER: _ClassVar[int]
    MAXMEMORY_FIELD_NUMBER: _ClassVar[int]
    MAXIOBPS_FIELD_NUMBER: _ClassVar[int]
    UPLOADS_FIELD_NUMBER: _ClassVar[int]
    SCHEDULE_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    VOLUMES_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    WORKDIR_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    SECRET_ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    WORKFLOWUUID_FIELD_NUMBER: _ClassVar[int]
    JOBUUID_FIELD_NUMBER: _ClassVar[int]
    REQUIREMENTS_FIELD_NUMBER: _ClassVar[int]
    GPU_COUNT_FIELD_NUMBER: _ClassVar[int]
    GPU_MEMORY_MB_FIELD_NUMBER: _ClassVar[int]
    name: str
    command: str
    args: _containers.RepeatedScalarFieldContainer[str]
    maxCpu: int
    cpuCores: str
    maxMemory: int
    maxIobps: int
    uploads: _containers.RepeatedCompositeFieldContainer[FileUpload]
    schedule: str
    network: str
    volumes: _containers.RepeatedScalarFieldContainer[str]
    runtime: str
    workDir: str
    environment: _containers.ScalarMap[str, str]
    secret_environment: _containers.ScalarMap[str, str]
    workflowUuid: str
    jobUuid: str
    requirements: _containers.RepeatedCompositeFieldContainer[JobRequirement]
    gpu_count: int
    gpu_memory_mb: int
    def __init__(self, name: _Optional[str] = ..., command: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ..., maxCpu: _Optional[int] = ..., cpuCores: _Optional[str] = ..., maxMemory: _Optional[int] = ..., maxIobps: _Optional[int] = ..., uploads: _Optional[_Iterable[_Union[FileUpload, _Mapping]]] = ..., schedule: _Optional[str] = ..., network: _Optional[str] = ..., volumes: _Optional[_Iterable[str]] = ..., runtime: _Optional[str] = ..., workDir: _Optional[str] = ..., environment: _Optional[_Mapping[str, str]] = ..., secret_environment: _Optional[_Mapping[str, str]] = ..., workflowUuid: _Optional[str] = ..., jobUuid: _Optional[str] = ..., requirements: _Optional[_Iterable[_Union[JobRequirement, _Mapping]]] = ..., gpu_count: _Optional[int] = ..., gpu_memory_mb: _Optional[int] = ...) -> None: ...

class RunJobResponse(_message.Message):
    __slots__ = ("jobUuid", "status", "command", "args", "maxCpu", "cpuCores", "maxMemory", "maxIobps", "startTime", "endTime", "exitCode", "scheduledTime")
    JOBUUID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    MAXCPU_FIELD_NUMBER: _ClassVar[int]
    CPUCORES_FIELD_NUMBER: _ClassVar[int]
    MAXMEMORY_FIELD_NUMBER: _ClassVar[int]
    MAXIOBPS_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    SCHEDULEDTIME_FIELD_NUMBER: _ClassVar[int]
    jobUuid: str
    status: str
    command: str
    args: _containers.RepeatedScalarFieldContainer[str]
    maxCpu: int
    cpuCores: str
    maxMemory: int
    maxIobps: int
    startTime: str
    endTime: str
    exitCode: int
    scheduledTime: str
    def __init__(self, jobUuid: _Optional[str] = ..., status: _Optional[str] = ..., command: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ..., maxCpu: _Optional[int] = ..., cpuCores: _Optional[str] = ..., maxMemory: _Optional[int] = ..., maxIobps: _Optional[int] = ..., startTime: _Optional[str] = ..., endTime: _Optional[str] = ..., exitCode: _Optional[int] = ..., scheduledTime: _Optional[str] = ...) -> None: ...

class JobRequirement(_message.Message):
    __slots__ = ("jobUuid", "status", "expression")
    JOBUUID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    EXPRESSION_FIELD_NUMBER: _ClassVar[int]
    jobUuid: str
    status: str
    expression: str
    def __init__(self, jobUuid: _Optional[str] = ..., status: _Optional[str] = ..., expression: _Optional[str] = ...) -> None: ...

class RunWorkflowRequest(_message.Message):
    __slots__ = ("workflow", "totalJobs", "jobOrder", "yamlContent", "workflowFiles")
    WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    TOTALJOBS_FIELD_NUMBER: _ClassVar[int]
    JOBORDER_FIELD_NUMBER: _ClassVar[int]
    YAMLCONTENT_FIELD_NUMBER: _ClassVar[int]
    WORKFLOWFILES_FIELD_NUMBER: _ClassVar[int]
    workflow: str
    totalJobs: int
    jobOrder: _containers.RepeatedScalarFieldContainer[str]
    yamlContent: str
    workflowFiles: _containers.RepeatedCompositeFieldContainer[FileUpload]
    def __init__(self, workflow: _Optional[str] = ..., totalJobs: _Optional[int] = ..., jobOrder: _Optional[_Iterable[str]] = ..., yamlContent: _Optional[str] = ..., workflowFiles: _Optional[_Iterable[_Union[FileUpload, _Mapping]]] = ...) -> None: ...

class RunWorkflowResponse(_message.Message):
    __slots__ = ("workflowUuid", "status")
    WORKFLOWUUID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    workflowUuid: str
    status: str
    def __init__(self, workflowUuid: _Optional[str] = ..., status: _Optional[str] = ...) -> None: ...

class GetWorkflowStatusRequest(_message.Message):
    __slots__ = ("workflowUuid",)
    WORKFLOWUUID_FIELD_NUMBER: _ClassVar[int]
    workflowUuid: str
    def __init__(self, workflowUuid: _Optional[str] = ...) -> None: ...

class GetWorkflowStatusResponse(_message.Message):
    __slots__ = ("workflow", "jobs")
    WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    JOBS_FIELD_NUMBER: _ClassVar[int]
    workflow: WorkflowInfo
    jobs: _containers.RepeatedCompositeFieldContainer[WorkflowJob]
    def __init__(self, workflow: _Optional[_Union[WorkflowInfo, _Mapping]] = ..., jobs: _Optional[_Iterable[_Union[WorkflowJob, _Mapping]]] = ...) -> None: ...

class ListWorkflowsRequest(_message.Message):
    __slots__ = ("includeCompleted",)
    INCLUDECOMPLETED_FIELD_NUMBER: _ClassVar[int]
    includeCompleted: bool
    def __init__(self, includeCompleted: bool = ...) -> None: ...

class ListWorkflowsResponse(_message.Message):
    __slots__ = ("workflows",)
    WORKFLOWS_FIELD_NUMBER: _ClassVar[int]
    workflows: _containers.RepeatedCompositeFieldContainer[WorkflowInfo]
    def __init__(self, workflows: _Optional[_Iterable[_Union[WorkflowInfo, _Mapping]]] = ...) -> None: ...

class GetWorkflowJobsRequest(_message.Message):
    __slots__ = ("workflowUuid",)
    WORKFLOWUUID_FIELD_NUMBER: _ClassVar[int]
    workflowUuid: str
    def __init__(self, workflowUuid: _Optional[str] = ...) -> None: ...

class GetWorkflowJobsResponse(_message.Message):
    __slots__ = ("jobs",)
    JOBS_FIELD_NUMBER: _ClassVar[int]
    jobs: _containers.RepeatedCompositeFieldContainer[WorkflowJob]
    def __init__(self, jobs: _Optional[_Iterable[_Union[WorkflowJob, _Mapping]]] = ...) -> None: ...

class WorkflowInfo(_message.Message):
    __slots__ = ("uuid", "status", "totalJobs", "completedJobs", "failedJobs", "canceledJobs", "createdAt", "startedAt", "completedAt", "yamlContent")
    UUID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TOTALJOBS_FIELD_NUMBER: _ClassVar[int]
    COMPLETEDJOBS_FIELD_NUMBER: _ClassVar[int]
    FAILEDJOBS_FIELD_NUMBER: _ClassVar[int]
    CANCELEDJOBS_FIELD_NUMBER: _ClassVar[int]
    CREATEDAT_FIELD_NUMBER: _ClassVar[int]
    STARTEDAT_FIELD_NUMBER: _ClassVar[int]
    COMPLETEDAT_FIELD_NUMBER: _ClassVar[int]
    YAMLCONTENT_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    status: str
    totalJobs: int
    completedJobs: int
    failedJobs: int
    canceledJobs: int
    createdAt: Timestamp
    startedAt: Timestamp
    completedAt: Timestamp
    yamlContent: str
    def __init__(self, uuid: _Optional[str] = ..., status: _Optional[str] = ..., totalJobs: _Optional[int] = ..., completedJobs: _Optional[int] = ..., failedJobs: _Optional[int] = ..., canceledJobs: _Optional[int] = ..., createdAt: _Optional[_Union[Timestamp, _Mapping]] = ..., startedAt: _Optional[_Union[Timestamp, _Mapping]] = ..., completedAt: _Optional[_Union[Timestamp, _Mapping]] = ..., yamlContent: _Optional[str] = ...) -> None: ...

class WorkflowJob(_message.Message):
    __slots__ = ("jobUuid", "jobName", "status", "dependencies", "startTime", "endTime", "exitCode")
    JOBUUID_FIELD_NUMBER: _ClassVar[int]
    JOBNAME_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCIES_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    jobUuid: str
    jobName: str
    status: str
    dependencies: _containers.RepeatedScalarFieldContainer[str]
    startTime: Timestamp
    endTime: Timestamp
    exitCode: int
    def __init__(self, jobUuid: _Optional[str] = ..., jobName: _Optional[str] = ..., status: _Optional[str] = ..., dependencies: _Optional[_Iterable[str]] = ..., startTime: _Optional[_Union[Timestamp, _Mapping]] = ..., endTime: _Optional[_Union[Timestamp, _Mapping]] = ..., exitCode: _Optional[int] = ...) -> None: ...

class Timestamp(_message.Message):
    __slots__ = ("seconds", "nanos")
    SECONDS_FIELD_NUMBER: _ClassVar[int]
    NANOS_FIELD_NUMBER: _ClassVar[int]
    seconds: int
    nanos: int
    def __init__(self, seconds: _Optional[int] = ..., nanos: _Optional[int] = ...) -> None: ...

class InstallRuntimeRequest(_message.Message):
    __slots__ = ("runtimeSpec", "repository", "branch", "path", "forceReinstall")
    RUNTIMESPEC_FIELD_NUMBER: _ClassVar[int]
    REPOSITORY_FIELD_NUMBER: _ClassVar[int]
    BRANCH_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    FORCEREINSTALL_FIELD_NUMBER: _ClassVar[int]
    runtimeSpec: str
    repository: str
    branch: str
    path: str
    forceReinstall: bool
    def __init__(self, runtimeSpec: _Optional[str] = ..., repository: _Optional[str] = ..., branch: _Optional[str] = ..., path: _Optional[str] = ..., forceReinstall: bool = ...) -> None: ...

class InstallRuntimeResponse(_message.Message):
    __slots__ = ("buildJobUuid", "runtimeSpec", "status", "message", "repository", "resolvedPath")
    BUILDJOBUUID_FIELD_NUMBER: _ClassVar[int]
    RUNTIMESPEC_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    REPOSITORY_FIELD_NUMBER: _ClassVar[int]
    RESOLVEDPATH_FIELD_NUMBER: _ClassVar[int]
    buildJobUuid: str
    runtimeSpec: str
    status: str
    message: str
    repository: str
    resolvedPath: str
    def __init__(self, buildJobUuid: _Optional[str] = ..., runtimeSpec: _Optional[str] = ..., status: _Optional[str] = ..., message: _Optional[str] = ..., repository: _Optional[str] = ..., resolvedPath: _Optional[str] = ...) -> None: ...

class InstallRuntimeFromLocalRequest(_message.Message):
    __slots__ = ("runtimeSpec", "files", "forceReinstall")
    RUNTIMESPEC_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    FORCEREINSTALL_FIELD_NUMBER: _ClassVar[int]
    runtimeSpec: str
    files: _containers.RepeatedCompositeFieldContainer[RuntimeFile]
    forceReinstall: bool
    def __init__(self, runtimeSpec: _Optional[str] = ..., files: _Optional[_Iterable[_Union[RuntimeFile, _Mapping]]] = ..., forceReinstall: bool = ...) -> None: ...

class RuntimeFile(_message.Message):
    __slots__ = ("path", "content", "executable")
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    EXECUTABLE_FIELD_NUMBER: _ClassVar[int]
    path: str
    content: bytes
    executable: bool
    def __init__(self, path: _Optional[str] = ..., content: _Optional[bytes] = ..., executable: bool = ...) -> None: ...

class ValidateRuntimeSpecRequest(_message.Message):
    __slots__ = ("runtimeSpec",)
    RUNTIMESPEC_FIELD_NUMBER: _ClassVar[int]
    runtimeSpec: str
    def __init__(self, runtimeSpec: _Optional[str] = ...) -> None: ...

class ValidateRuntimeSpecResponse(_message.Message):
    __slots__ = ("valid", "message", "normalizedSpec", "specInfo")
    VALID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NORMALIZEDSPEC_FIELD_NUMBER: _ClassVar[int]
    SPECINFO_FIELD_NUMBER: _ClassVar[int]
    valid: bool
    message: str
    normalizedSpec: str
    specInfo: RuntimeSpecInfo
    def __init__(self, valid: bool = ..., message: _Optional[str] = ..., normalizedSpec: _Optional[str] = ..., specInfo: _Optional[_Union[RuntimeSpecInfo, _Mapping]] = ...) -> None: ...

class RuntimeRemoveReq(_message.Message):
    __slots__ = ("runtime",)
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    runtime: str
    def __init__(self, runtime: _Optional[str] = ...) -> None: ...

class RuntimeRemoveRes(_message.Message):
    __slots__ = ("success", "message", "freedSpaceBytes")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FREEDSPACEBYTES_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    freedSpaceBytes: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., freedSpaceBytes: _Optional[int] = ...) -> None: ...

class RuntimeSpecInfo(_message.Message):
    __slots__ = ("language", "version", "variants", "architecture")
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    VARIANTS_FIELD_NUMBER: _ClassVar[int]
    ARCHITECTURE_FIELD_NUMBER: _ClassVar[int]
    language: str
    version: str
    variants: _containers.RepeatedScalarFieldContainer[str]
    architecture: str
    def __init__(self, language: _Optional[str] = ..., version: _Optional[str] = ..., variants: _Optional[_Iterable[str]] = ..., architecture: _Optional[str] = ...) -> None: ...

class JobMetricsRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class JobMetricsSummaryRequest(_message.Message):
    __slots__ = ("uuid", "periodSeconds")
    UUID_FIELD_NUMBER: _ClassVar[int]
    PERIODSECONDS_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    periodSeconds: int
    def __init__(self, uuid: _Optional[str] = ..., periodSeconds: _Optional[int] = ...) -> None: ...

class JobMetricsSummaryResponse(_message.Message):
    __slots__ = ("cpu", "memory", "io", "network")
    CPU_FIELD_NUMBER: _ClassVar[int]
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    IO_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    cpu: JobMetricsAggregate
    memory: JobMetricsAggregate
    io: JobMetricsAggregate
    network: JobMetricsAggregate
    def __init__(self, cpu: _Optional[_Union[JobMetricsAggregate, _Mapping]] = ..., memory: _Optional[_Union[JobMetricsAggregate, _Mapping]] = ..., io: _Optional[_Union[JobMetricsAggregate, _Mapping]] = ..., network: _Optional[_Union[JobMetricsAggregate, _Mapping]] = ...) -> None: ...

class JobMetricsSample(_message.Message):
    __slots__ = ("jobId", "timestamp", "sampleIntervalSeconds", "cpu", "memory", "io", "network", "process", "gpu", "cgroupPath", "limits", "gpuAllocation")
    JOBID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SAMPLEINTERVALSECONDS_FIELD_NUMBER: _ClassVar[int]
    CPU_FIELD_NUMBER: _ClassVar[int]
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    IO_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    PROCESS_FIELD_NUMBER: _ClassVar[int]
    GPU_FIELD_NUMBER: _ClassVar[int]
    CGROUPPATH_FIELD_NUMBER: _ClassVar[int]
    LIMITS_FIELD_NUMBER: _ClassVar[int]
    GPUALLOCATION_FIELD_NUMBER: _ClassVar[int]
    jobId: str
    timestamp: int
    sampleIntervalSeconds: int
    cpu: JobCPUMetrics
    memory: JobMemoryMetrics
    io: JobIOMetrics
    network: JobNetworkMetrics
    process: JobProcessMetrics
    gpu: _containers.RepeatedCompositeFieldContainer[JobGPUMetrics]
    cgroupPath: str
    limits: JobResourceLimits
    gpuAllocation: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, jobId: _Optional[str] = ..., timestamp: _Optional[int] = ..., sampleIntervalSeconds: _Optional[int] = ..., cpu: _Optional[_Union[JobCPUMetrics, _Mapping]] = ..., memory: _Optional[_Union[JobMemoryMetrics, _Mapping]] = ..., io: _Optional[_Union[JobIOMetrics, _Mapping]] = ..., network: _Optional[_Union[JobNetworkMetrics, _Mapping]] = ..., process: _Optional[_Union[JobProcessMetrics, _Mapping]] = ..., gpu: _Optional[_Iterable[_Union[JobGPUMetrics, _Mapping]]] = ..., cgroupPath: _Optional[str] = ..., limits: _Optional[_Union[JobResourceLimits, _Mapping]] = ..., gpuAllocation: _Optional[_Iterable[int]] = ...) -> None: ...

class JobResourceLimits(_message.Message):
    __slots__ = ("cpu", "memory", "io")
    CPU_FIELD_NUMBER: _ClassVar[int]
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    IO_FIELD_NUMBER: _ClassVar[int]
    cpu: int
    memory: int
    io: int
    def __init__(self, cpu: _Optional[int] = ..., memory: _Optional[int] = ..., io: _Optional[int] = ...) -> None: ...

class JobCPUMetrics(_message.Message):
    __slots__ = ("usageUsec", "userUsec", "systemUsec", "nrPeriods", "nrThrottled", "throttledUsec", "usagePercent", "throttlePercent", "pressureSome10", "pressureSome60", "pressureSome300", "pressureFull10", "pressureFull60", "pressureFull300")
    USAGEUSEC_FIELD_NUMBER: _ClassVar[int]
    USERUSEC_FIELD_NUMBER: _ClassVar[int]
    SYSTEMUSEC_FIELD_NUMBER: _ClassVar[int]
    NRPERIODS_FIELD_NUMBER: _ClassVar[int]
    NRTHROTTLED_FIELD_NUMBER: _ClassVar[int]
    THROTTLEDUSEC_FIELD_NUMBER: _ClassVar[int]
    USAGEPERCENT_FIELD_NUMBER: _ClassVar[int]
    THROTTLEPERCENT_FIELD_NUMBER: _ClassVar[int]
    PRESSURESOME10_FIELD_NUMBER: _ClassVar[int]
    PRESSURESOME60_FIELD_NUMBER: _ClassVar[int]
    PRESSURESOME300_FIELD_NUMBER: _ClassVar[int]
    PRESSUREFULL10_FIELD_NUMBER: _ClassVar[int]
    PRESSUREFULL60_FIELD_NUMBER: _ClassVar[int]
    PRESSUREFULL300_FIELD_NUMBER: _ClassVar[int]
    usageUsec: int
    userUsec: int
    systemUsec: int
    nrPeriods: int
    nrThrottled: int
    throttledUsec: int
    usagePercent: float
    throttlePercent: float
    pressureSome10: float
    pressureSome60: float
    pressureSome300: float
    pressureFull10: float
    pressureFull60: float
    pressureFull300: float
    def __init__(self, usageUsec: _Optional[int] = ..., userUsec: _Optional[int] = ..., systemUsec: _Optional[int] = ..., nrPeriods: _Optional[int] = ..., nrThrottled: _Optional[int] = ..., throttledUsec: _Optional[int] = ..., usagePercent: _Optional[float] = ..., throttlePercent: _Optional[float] = ..., pressureSome10: _Optional[float] = ..., pressureSome60: _Optional[float] = ..., pressureSome300: _Optional[float] = ..., pressureFull10: _Optional[float] = ..., pressureFull60: _Optional[float] = ..., pressureFull300: _Optional[float] = ...) -> None: ...

class JobMemoryMetrics(_message.Message):
    __slots__ = ("current", "max", "usagePercent", "anon", "file", "kernelStack", "slab", "sock", "shmem", "fileMapped", "fileDirty", "fileWriteback", "pgFault", "pgMajFault", "oomEvents", "oomKill", "pressureSome10", "pressureSome60", "pressureSome300", "pressureFull10", "pressureFull60", "pressureFull300")
    CURRENT_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    USAGEPERCENT_FIELD_NUMBER: _ClassVar[int]
    ANON_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    KERNELSTACK_FIELD_NUMBER: _ClassVar[int]
    SLAB_FIELD_NUMBER: _ClassVar[int]
    SOCK_FIELD_NUMBER: _ClassVar[int]
    SHMEM_FIELD_NUMBER: _ClassVar[int]
    FILEMAPPED_FIELD_NUMBER: _ClassVar[int]
    FILEDIRTY_FIELD_NUMBER: _ClassVar[int]
    FILEWRITEBACK_FIELD_NUMBER: _ClassVar[int]
    PGFAULT_FIELD_NUMBER: _ClassVar[int]
    PGMAJFAULT_FIELD_NUMBER: _ClassVar[int]
    OOMEVENTS_FIELD_NUMBER: _ClassVar[int]
    OOMKILL_FIELD_NUMBER: _ClassVar[int]
    PRESSURESOME10_FIELD_NUMBER: _ClassVar[int]
    PRESSURESOME60_FIELD_NUMBER: _ClassVar[int]
    PRESSURESOME300_FIELD_NUMBER: _ClassVar[int]
    PRESSUREFULL10_FIELD_NUMBER: _ClassVar[int]
    PRESSUREFULL60_FIELD_NUMBER: _ClassVar[int]
    PRESSUREFULL300_FIELD_NUMBER: _ClassVar[int]
    current: int
    max: int
    usagePercent: float
    anon: int
    file: int
    kernelStack: int
    slab: int
    sock: int
    shmem: int
    fileMapped: int
    fileDirty: int
    fileWriteback: int
    pgFault: int
    pgMajFault: int
    oomEvents: int
    oomKill: int
    pressureSome10: float
    pressureSome60: float
    pressureSome300: float
    pressureFull10: float
    pressureFull60: float
    pressureFull300: float
    def __init__(self, current: _Optional[int] = ..., max: _Optional[int] = ..., usagePercent: _Optional[float] = ..., anon: _Optional[int] = ..., file: _Optional[int] = ..., kernelStack: _Optional[int] = ..., slab: _Optional[int] = ..., sock: _Optional[int] = ..., shmem: _Optional[int] = ..., fileMapped: _Optional[int] = ..., fileDirty: _Optional[int] = ..., fileWriteback: _Optional[int] = ..., pgFault: _Optional[int] = ..., pgMajFault: _Optional[int] = ..., oomEvents: _Optional[int] = ..., oomKill: _Optional[int] = ..., pressureSome10: _Optional[float] = ..., pressureSome60: _Optional[float] = ..., pressureSome300: _Optional[float] = ..., pressureFull10: _Optional[float] = ..., pressureFull60: _Optional[float] = ..., pressureFull300: _Optional[float] = ...) -> None: ...

class JobIOMetrics(_message.Message):
    __slots__ = ("devices", "totalReadBytes", "totalWriteBytes", "totalReadOps", "totalWriteOps", "totalDiscardBytes", "totalDiscardOps", "readBPS", "writeBPS", "readIOPS", "writeIOPS", "pressureSome10", "pressureSome60", "pressureSome300", "pressureFull10", "pressureFull60", "pressureFull300")
    class DevicesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: DeviceIOMetrics
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[DeviceIOMetrics, _Mapping]] = ...) -> None: ...
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    TOTALREADBYTES_FIELD_NUMBER: _ClassVar[int]
    TOTALWRITEBYTES_FIELD_NUMBER: _ClassVar[int]
    TOTALREADOPS_FIELD_NUMBER: _ClassVar[int]
    TOTALWRITEOPS_FIELD_NUMBER: _ClassVar[int]
    TOTALDISCARDBYTES_FIELD_NUMBER: _ClassVar[int]
    TOTALDISCARDOPS_FIELD_NUMBER: _ClassVar[int]
    READBPS_FIELD_NUMBER: _ClassVar[int]
    WRITEBPS_FIELD_NUMBER: _ClassVar[int]
    READIOPS_FIELD_NUMBER: _ClassVar[int]
    WRITEIOPS_FIELD_NUMBER: _ClassVar[int]
    PRESSURESOME10_FIELD_NUMBER: _ClassVar[int]
    PRESSURESOME60_FIELD_NUMBER: _ClassVar[int]
    PRESSURESOME300_FIELD_NUMBER: _ClassVar[int]
    PRESSUREFULL10_FIELD_NUMBER: _ClassVar[int]
    PRESSUREFULL60_FIELD_NUMBER: _ClassVar[int]
    PRESSUREFULL300_FIELD_NUMBER: _ClassVar[int]
    devices: _containers.MessageMap[str, DeviceIOMetrics]
    totalReadBytes: int
    totalWriteBytes: int
    totalReadOps: int
    totalWriteOps: int
    totalDiscardBytes: int
    totalDiscardOps: int
    readBPS: float
    writeBPS: float
    readIOPS: float
    writeIOPS: float
    pressureSome10: float
    pressureSome60: float
    pressureSome300: float
    pressureFull10: float
    pressureFull60: float
    pressureFull300: float
    def __init__(self, devices: _Optional[_Mapping[str, DeviceIOMetrics]] = ..., totalReadBytes: _Optional[int] = ..., totalWriteBytes: _Optional[int] = ..., totalReadOps: _Optional[int] = ..., totalWriteOps: _Optional[int] = ..., totalDiscardBytes: _Optional[int] = ..., totalDiscardOps: _Optional[int] = ..., readBPS: _Optional[float] = ..., writeBPS: _Optional[float] = ..., readIOPS: _Optional[float] = ..., writeIOPS: _Optional[float] = ..., pressureSome10: _Optional[float] = ..., pressureSome60: _Optional[float] = ..., pressureSome300: _Optional[float] = ..., pressureFull10: _Optional[float] = ..., pressureFull60: _Optional[float] = ..., pressureFull300: _Optional[float] = ...) -> None: ...

class DeviceIOMetrics(_message.Message):
    __slots__ = ("device", "readBytes", "writeBytes", "readOps", "writeOps", "discardBytes", "discardOps")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    READBYTES_FIELD_NUMBER: _ClassVar[int]
    WRITEBYTES_FIELD_NUMBER: _ClassVar[int]
    READOPS_FIELD_NUMBER: _ClassVar[int]
    WRITEOPS_FIELD_NUMBER: _ClassVar[int]
    DISCARDBYTES_FIELD_NUMBER: _ClassVar[int]
    DISCARDOPS_FIELD_NUMBER: _ClassVar[int]
    device: str
    readBytes: int
    writeBytes: int
    readOps: int
    writeOps: int
    discardBytes: int
    discardOps: int
    def __init__(self, device: _Optional[str] = ..., readBytes: _Optional[int] = ..., writeBytes: _Optional[int] = ..., readOps: _Optional[int] = ..., writeOps: _Optional[int] = ..., discardBytes: _Optional[int] = ..., discardOps: _Optional[int] = ...) -> None: ...

class JobNetworkMetrics(_message.Message):
    __slots__ = ("interfaces", "totalRxBytes", "totalTxBytes", "totalRxPackets", "totalTxPackets", "totalRxErrors", "totalTxErrors", "totalRxDropped", "totalTxDropped", "rxBPS", "txBPS")
    class InterfacesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: NetworkInterfaceMetrics
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[NetworkInterfaceMetrics, _Mapping]] = ...) -> None: ...
    INTERFACES_FIELD_NUMBER: _ClassVar[int]
    TOTALRXBYTES_FIELD_NUMBER: _ClassVar[int]
    TOTALTXBYTES_FIELD_NUMBER: _ClassVar[int]
    TOTALRXPACKETS_FIELD_NUMBER: _ClassVar[int]
    TOTALTXPACKETS_FIELD_NUMBER: _ClassVar[int]
    TOTALRXERRORS_FIELD_NUMBER: _ClassVar[int]
    TOTALTXERRORS_FIELD_NUMBER: _ClassVar[int]
    TOTALRXDROPPED_FIELD_NUMBER: _ClassVar[int]
    TOTALTXDROPPED_FIELD_NUMBER: _ClassVar[int]
    RXBPS_FIELD_NUMBER: _ClassVar[int]
    TXBPS_FIELD_NUMBER: _ClassVar[int]
    interfaces: _containers.MessageMap[str, NetworkInterfaceMetrics]
    totalRxBytes: int
    totalTxBytes: int
    totalRxPackets: int
    totalTxPackets: int
    totalRxErrors: int
    totalTxErrors: int
    totalRxDropped: int
    totalTxDropped: int
    rxBPS: float
    txBPS: float
    def __init__(self, interfaces: _Optional[_Mapping[str, NetworkInterfaceMetrics]] = ..., totalRxBytes: _Optional[int] = ..., totalTxBytes: _Optional[int] = ..., totalRxPackets: _Optional[int] = ..., totalTxPackets: _Optional[int] = ..., totalRxErrors: _Optional[int] = ..., totalTxErrors: _Optional[int] = ..., totalRxDropped: _Optional[int] = ..., totalTxDropped: _Optional[int] = ..., rxBPS: _Optional[float] = ..., txBPS: _Optional[float] = ...) -> None: ...

class NetworkInterfaceMetrics(_message.Message):
    __slots__ = ("interface", "rxBytes", "txBytes", "rxPackets", "txPackets", "rxErrors", "txErrors", "rxDropped", "txDropped")
    INTERFACE_FIELD_NUMBER: _ClassVar[int]
    RXBYTES_FIELD_NUMBER: _ClassVar[int]
    TXBYTES_FIELD_NUMBER: _ClassVar[int]
    RXPACKETS_FIELD_NUMBER: _ClassVar[int]
    TXPACKETS_FIELD_NUMBER: _ClassVar[int]
    RXERRORS_FIELD_NUMBER: _ClassVar[int]
    TXERRORS_FIELD_NUMBER: _ClassVar[int]
    RXDROPPED_FIELD_NUMBER: _ClassVar[int]
    TXDROPPED_FIELD_NUMBER: _ClassVar[int]
    interface: str
    rxBytes: int
    txBytes: int
    rxPackets: int
    txPackets: int
    rxErrors: int
    txErrors: int
    rxDropped: int
    txDropped: int
    def __init__(self, interface: _Optional[str] = ..., rxBytes: _Optional[int] = ..., txBytes: _Optional[int] = ..., rxPackets: _Optional[int] = ..., txPackets: _Optional[int] = ..., rxErrors: _Optional[int] = ..., txErrors: _Optional[int] = ..., rxDropped: _Optional[int] = ..., txDropped: _Optional[int] = ...) -> None: ...

class JobProcessMetrics(_message.Message):
    __slots__ = ("current", "max", "events", "threads", "running", "sleeping", "stopped", "zombie", "openFDs", "maxFDs")
    CURRENT_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    THREADS_FIELD_NUMBER: _ClassVar[int]
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    SLEEPING_FIELD_NUMBER: _ClassVar[int]
    STOPPED_FIELD_NUMBER: _ClassVar[int]
    ZOMBIE_FIELD_NUMBER: _ClassVar[int]
    OPENFDS_FIELD_NUMBER: _ClassVar[int]
    MAXFDS_FIELD_NUMBER: _ClassVar[int]
    current: int
    max: int
    events: int
    threads: int
    running: int
    sleeping: int
    stopped: int
    zombie: int
    openFDs: int
    maxFDs: int
    def __init__(self, current: _Optional[int] = ..., max: _Optional[int] = ..., events: _Optional[int] = ..., threads: _Optional[int] = ..., running: _Optional[int] = ..., sleeping: _Optional[int] = ..., stopped: _Optional[int] = ..., zombie: _Optional[int] = ..., openFDs: _Optional[int] = ..., maxFDs: _Optional[int] = ...) -> None: ...

class JobGPUMetrics(_message.Message):
    __slots__ = ("index", "uuid", "name", "computeCapability", "driverVersion", "utilization", "memoryUsed", "memoryTotal", "memoryFree", "memoryPercent", "encoderUtil", "decoderUtil", "smClock", "memoryClock", "pcieThroughputRx", "pcieThroughputTx", "temperature", "temperatureMemory", "powerDraw", "powerLimit", "fanSpeed", "eccErrorsSingle", "eccErrorsDouble", "xidErrors", "retiredPages", "throttleReasons", "processesCount", "processesMemory", "computeMode")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMPUTECAPABILITY_FIELD_NUMBER: _ClassVar[int]
    DRIVERVERSION_FIELD_NUMBER: _ClassVar[int]
    UTILIZATION_FIELD_NUMBER: _ClassVar[int]
    MEMORYUSED_FIELD_NUMBER: _ClassVar[int]
    MEMORYTOTAL_FIELD_NUMBER: _ClassVar[int]
    MEMORYFREE_FIELD_NUMBER: _ClassVar[int]
    MEMORYPERCENT_FIELD_NUMBER: _ClassVar[int]
    ENCODERUTIL_FIELD_NUMBER: _ClassVar[int]
    DECODERUTIL_FIELD_NUMBER: _ClassVar[int]
    SMCLOCK_FIELD_NUMBER: _ClassVar[int]
    MEMORYCLOCK_FIELD_NUMBER: _ClassVar[int]
    PCIETHROUGHPUTRX_FIELD_NUMBER: _ClassVar[int]
    PCIETHROUGHPUTTX_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    TEMPERATUREMEMORY_FIELD_NUMBER: _ClassVar[int]
    POWERDRAW_FIELD_NUMBER: _ClassVar[int]
    POWERLIMIT_FIELD_NUMBER: _ClassVar[int]
    FANSPEED_FIELD_NUMBER: _ClassVar[int]
    ECCERRORSSINGLE_FIELD_NUMBER: _ClassVar[int]
    ECCERRORSDOUBLE_FIELD_NUMBER: _ClassVar[int]
    XIDERRORS_FIELD_NUMBER: _ClassVar[int]
    RETIREDPAGES_FIELD_NUMBER: _ClassVar[int]
    THROTTLEREASONS_FIELD_NUMBER: _ClassVar[int]
    PROCESSESCOUNT_FIELD_NUMBER: _ClassVar[int]
    PROCESSESMEMORY_FIELD_NUMBER: _ClassVar[int]
    COMPUTEMODE_FIELD_NUMBER: _ClassVar[int]
    index: int
    uuid: str
    name: str
    computeCapability: str
    driverVersion: str
    utilization: float
    memoryUsed: int
    memoryTotal: int
    memoryFree: int
    memoryPercent: float
    encoderUtil: float
    decoderUtil: float
    smClock: int
    memoryClock: int
    pcieThroughputRx: float
    pcieThroughputTx: float
    temperature: float
    temperatureMemory: float
    powerDraw: float
    powerLimit: float
    fanSpeed: float
    eccErrorsSingle: int
    eccErrorsDouble: int
    xidErrors: int
    retiredPages: int
    throttleReasons: int
    processesCount: int
    processesMemory: int
    computeMode: str
    def __init__(self, index: _Optional[int] = ..., uuid: _Optional[str] = ..., name: _Optional[str] = ..., computeCapability: _Optional[str] = ..., driverVersion: _Optional[str] = ..., utilization: _Optional[float] = ..., memoryUsed: _Optional[int] = ..., memoryTotal: _Optional[int] = ..., memoryFree: _Optional[int] = ..., memoryPercent: _Optional[float] = ..., encoderUtil: _Optional[float] = ..., decoderUtil: _Optional[float] = ..., smClock: _Optional[int] = ..., memoryClock: _Optional[int] = ..., pcieThroughputRx: _Optional[float] = ..., pcieThroughputTx: _Optional[float] = ..., temperature: _Optional[float] = ..., temperatureMemory: _Optional[float] = ..., powerDraw: _Optional[float] = ..., powerLimit: _Optional[float] = ..., fanSpeed: _Optional[float] = ..., eccErrorsSingle: _Optional[int] = ..., eccErrorsDouble: _Optional[int] = ..., xidErrors: _Optional[int] = ..., retiredPages: _Optional[int] = ..., throttleReasons: _Optional[int] = ..., processesCount: _Optional[int] = ..., processesMemory: _Optional[int] = ..., computeMode: _Optional[str] = ...) -> None: ...

class JobMetricsAggregate(_message.Message):
    __slots__ = ("min", "max", "avg", "p50", "p95", "p99")
    MIN_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    AVG_FIELD_NUMBER: _ClassVar[int]
    P50_FIELD_NUMBER: _ClassVar[int]
    P95_FIELD_NUMBER: _ClassVar[int]
    P99_FIELD_NUMBER: _ClassVar[int]
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float
    def __init__(self, min: _Optional[float] = ..., max: _Optional[float] = ..., avg: _Optional[float] = ..., p50: _Optional[float] = ..., p95: _Optional[float] = ..., p99: _Optional[float] = ...) -> None: ...
