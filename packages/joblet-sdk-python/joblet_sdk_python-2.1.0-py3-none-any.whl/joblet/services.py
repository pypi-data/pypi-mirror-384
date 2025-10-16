"""Service classes for Joblet SDK"""

from datetime import datetime
from typing import Any, Callable, Dict, Iterator, List, Optional, cast

import grpc

from .exceptions import (
    JobNotFoundError,
    NetworkError,
    RuntimeNotFoundError,
    ValidationError,
    VolumeError,
    WorkflowNotFoundError,
)
from .proto import joblet_pb2, joblet_pb2_grpc, persist_pb2, persist_pb2_grpc


class JobService:
    """Service for managing jobs and workflows"""

    def __init__(
        self, channel: grpc.Channel, persist_service_getter: Optional[Callable] = None
    ):
        self.stub = joblet_pb2_grpc.JobServiceStub(channel)
        self._persist_service_getter = persist_service_getter

    @property
    def _persist_service(self):
        """Lazy access to persist service to avoid circular dependency"""
        if self._persist_service_getter:
            try:
                return self._persist_service_getter()
            except Exception:
                return None
        return None

    def run_job(
        self,
        command: str,
        args: Optional[List[str]] = None,
        name: Optional[str] = None,
        max_cpu: Optional[int] = None,
        cpu_cores: Optional[str] = None,
        max_memory: Optional[int] = None,
        max_iobps: Optional[int] = None,
        schedule: Optional[str] = None,
        network: Optional[str] = None,
        volumes: Optional[List[str]] = None,
        runtime: Optional[str] = None,
        work_dir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        secret_environment: Optional[Dict[str, str]] = None,
        uploads: Optional[List[Dict[str, Any]]] = None,
        gpu_count: Optional[int] = None,
        gpu_memory_mb: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run a new job

        Args:
            command: Command to execute
            args: Command arguments
            name: Job name
            max_cpu: Maximum CPU percentage
            cpu_cores: CPU cores specification
            max_memory: Maximum memory in MB
            max_iobps: Maximum IO operations per second
            schedule: Schedule time (RFC3339)
            network: Network configuration
            volumes: List of volumes to mount
            runtime: Runtime specification
            work_dir: Working directory
            environment: Environment variables
            secret_environment: Secret environment variables
            uploads: Files to upload
            gpu_count: Number of GPUs to allocate
            gpu_memory_mb: Minimum GPU memory required in MB

        Returns:
            Job response dictionary
        """
        request = joblet_pb2.RunJobRequest(
            command=command,
            args=args or [],
            name=name or "",
            maxCpu=max_cpu or 0,
            cpuCores=cpu_cores or "",
            maxMemory=max_memory or 0,
            maxIobps=max_iobps or 0,
            schedule=schedule or "",
            network=network or "",
            volumes=volumes or [],
            runtime=runtime or "",
            workDir=work_dir or "",
            environment=environment or {},
            secret_environment=secret_environment or {},
            gpu_count=gpu_count or 0,
            gpu_memory_mb=gpu_memory_mb or 0,
        )

        # Add file uploads if provided
        if uploads:
            for upload in uploads:
                file_upload = joblet_pb2.FileUpload(
                    path=upload.get("path", ""),
                    content=upload.get("content", b""),
                    mode=upload.get("mode", 0o644),
                    isDirectory=upload.get("is_directory", False),
                )
                request.uploads.append(file_upload)

        try:
            response = self.stub.RunJob(request)
            return {
                "job_uuid": response.jobUuid,
                "status": response.status,
                "command": response.command,
                "args": list(response.args),
                "max_cpu": response.maxCpu,
                "cpu_cores": response.cpuCores,
                "max_memory": response.maxMemory,
                "max_iobps": response.maxIobps,
                "start_time": response.startTime,
                "end_time": response.endTime,
                "exit_code": response.exitCode,
                "scheduled_time": response.scheduledTime,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to run job: {e.details()}")

    def get_job_status(self, job_uuid: str) -> Dict[str, Any]:
        """Get job status

        Args:
            job_uuid: Job UUID

        Returns:
            Job status dictionary
        """
        request = joblet_pb2.GetJobStatusReq(uuid=job_uuid)

        try:
            response = self.stub.GetJobStatus(request)
            return {
                "uuid": response.uuid,
                "name": response.name,
                "command": response.command,
                "args": list(response.args),
                "max_cpu": response.maxCPU,
                "cpu_cores": response.cpuCores,
                "max_memory": response.maxMemory,
                "max_iobps": response.maxIOBPS,
                "status": response.status,
                "start_time": response.startTime,
                "end_time": response.endTime,
                "exit_code": response.exitCode,
                "scheduled_time": response.scheduledTime,
                "environment": dict(response.environment),
                "secret_environment": dict(response.secret_environment),
                "network": response.network,
                "volumes": list(response.volumes),
                "runtime": response.runtime,
                "work_dir": response.workDir,
                "uploads": list(response.uploads),
                "dependencies": list(response.dependencies),
                "workflow_uuid": response.workflowUuid,
                "gpu_indices": list(response.gpu_indices),
                "gpu_count": response.gpu_count,
                "gpu_memory_mb": response.gpu_memory_mb,
                "node_id": response.nodeId,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Job {job_uuid} not found: {e.details()}")

    def stop_job(self, job_uuid: str) -> Dict[str, Any]:
        """Stop a running job

        Args:
            job_uuid: Job UUID

        Returns:
            Stop response dictionary
        """
        request = joblet_pb2.StopJobReq(uuid=job_uuid)

        try:
            response = self.stub.StopJob(request)
            return {
                "uuid": response.uuid,
                "status": response.status,
                "end_time": response.endTime,
                "exit_code": response.exitCode,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to stop job {job_uuid}: {e.details()}")

    def cancel_job(self, job_uuid: str) -> Dict[str, Any]:
        """Cancel a scheduled job

        This is specifically for jobs in SCHEDULED status. It will:
        - Cancel the job (preventing it from executing)
        - Change status to CANCELED (not STOPPED)
        - Preserve the job in history for audit

        Args:
            job_uuid: Job UUID

        Returns:
            Cancel response dictionary with uuid, status

        Raises:
            JobNotFoundError: If job not found or not scheduled
        """
        request = joblet_pb2.CancelJobReq(uuid=job_uuid)

        try:
            response = self.stub.CancelJob(request)
            return {
                "uuid": response.uuid,
                "status": response.status,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to cancel job {job_uuid}: {e.details()}")

    def delete_job(self, job_uuid: str) -> Dict[str, Any]:
        """Delete a job

        Args:
            job_uuid: Job UUID

        Returns:
            Delete response dictionary
        """
        request = joblet_pb2.DeleteJobReq(uuid=job_uuid)

        try:
            response = self.stub.DeleteJob(request)
            return {
                "uuid": response.uuid,
                "success": response.success,
                "message": response.message,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to delete job {job_uuid}: {e.details()}")

    def delete_all_jobs(self) -> Dict[str, Any]:
        """Delete all non-running jobs

        Returns:
            Delete response dictionary
        """
        request = joblet_pb2.DeleteAllJobsReq()

        try:
            response = self.stub.DeleteAllJobs(request)
            return {
                "success": response.success,
                "message": response.message,
                "deleted_count": response.deleted_count,
                "skipped_count": response.skipped_count,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to delete all jobs: {e.details()}")

    def get_job_logs(
        self, job_uuid: str, include_historical: bool = True
    ) -> Iterator[bytes]:
        """Stream job logs with automatic historical + live log handling

        This method intelligently handles both historical and live logs:
        1. First fetches any historical logs from persist service (if available)
        2. Then streams live logs from the job service

        This provides seamless log access for both completed and running jobs,
        similar to how 'rnx job log' works.

        Args:
            job_uuid: Job UUID or short UUID prefix
            include_historical: If True, fetch historical logs first (default: True)

        Yields:
            bytes: Log chunks from both historical and live sources

        Raises:
            JobNotFoundError: If the job doesn't exist

        Example:
            >>> # Get all logs (historical + live) for any job
            >>> for chunk in client.jobs.get_job_logs(job_uuid):
            ...     print(chunk.decode('utf-8'), end='')
            ...
            >>> # Get only live logs (skip historical)
            >>> for chunk in client.jobs.get_job_logs(
            ...     job_uuid, include_historical=False
            ... ):
            ...     print(chunk.decode('utf-8'), end='')
        """
        # Step 1: Try to fetch historical logs from persist service first
        if include_historical and self._persist_service:
            try:
                for log_line in self._persist_service.query_logs(job_id=job_uuid):
                    # Yield historical log content
                    yield log_line["content"]
            except grpc.RpcError as e:
                # Gracefully handle persist service errors
                # - Not implemented: persist service doesn't have this feature yet
                # - Unavailable: persist service is not running
                # - Not found: no historical logs exist for this job
                # All these are OK - we'll just stream live logs
                if e.code() not in [
                    grpc.StatusCode.UNIMPLEMENTED,
                    grpc.StatusCode.UNAVAILABLE,
                    grpc.StatusCode.NOT_FOUND,
                ]:
                    # For unexpected errors, log but continue
                    import sys

                    print(
                        f"⚠️  Warning: couldn't fetch historical logs: "
                        f"{e.details()}",
                        file=sys.stderr,
                    )
            except Exception:
                # Any other error (e.g., persist not configured)
                # Continue silently
                pass

        # Step 2: Stream live logs from joblet-core
        request = joblet_pb2.GetJobLogsReq(uuid=job_uuid)

        try:
            for chunk in self.stub.GetJobLogs(request):
                yield chunk.payload
        except grpc.RpcError as e:
            raise JobNotFoundError(
                f"Failed to get logs for job {job_uuid}: {e.details()}"
            )

    def stream_live_logs(self, job_uuid: str) -> Iterator[bytes]:
        """Stream live logs only (skip historical logs)

        This method only streams logs from the live job service, skipping
        any historical logs. Useful when you only want to see new output.

        Args:
            job_uuid: Job UUID or short UUID prefix

        Yields:
            bytes: Log chunks as they arrive from the job

        Raises:
            JobNotFoundError: If the job doesn't exist

        Example:
            >>> for chunk in client.jobs.stream_live_logs(job_uuid):
            ...     print(chunk.decode('utf-8'), end='')
        """
        return self.get_job_logs(job_uuid, include_historical=False)

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs on the server

        Retrieves a list of all jobs including their status, resource usage,
        and metadata. Jobs are returned in creation order.

        Returns:
            List[Dict[str, Any]]: List of job dictionaries containing:
                - uuid: Job unique identifier
                - name: Job name
                - status: Current status (pending, running, completed, failed, etc.)
                - command: Executed command
                - start_time: When the job started
                - exit_code: Exit code (if completed)

        Raises:
            JobNotFoundError: If unable to retrieve job list

        Example:
            >>> jobs = client.jobs.list_jobs()
            >>> for job in jobs:
            ...     print(f"{job['name']}: {job['status']}")
        """
        request = joblet_pb2.EmptyRequest()

        try:
            response = self.stub.ListJobs(request)
            jobs = []
            for job in response.jobs:
                jobs.append(
                    {
                        "uuid": job.uuid,
                        "name": job.name,
                        "command": job.command,
                        "args": list(job.args),
                        "max_cpu": job.maxCPU,
                        "cpu_cores": job.cpuCores,
                        "max_memory": job.maxMemory,
                        "max_iobps": job.maxIOBPS,
                        "status": job.status,
                        "start_time": job.startTime,
                        "end_time": job.endTime,
                        "exit_code": job.exitCode,
                        "scheduled_time": job.scheduledTime,
                        "runtime": job.runtime,
                        "environment": dict(job.environment),
                        "secret_environment": dict(job.secret_environment),
                        "gpu_indices": list(job.gpu_indices),
                        "gpu_count": job.gpu_count,
                        "gpu_memory_mb": job.gpu_memory_mb,
                        "node_id": job.nodeId,
                    }
                )
            return jobs
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to list jobs: {e.details()}")

    def run_workflow(
        self,
        workflow: str,
        yaml_content: Optional[str] = None,
        workflow_files: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Run a workflow

        Args:
            workflow: Workflow filename
            yaml_content: YAML content
            workflow_files: Workflow files to upload

        Returns:
            Workflow response dictionary
        """
        request = joblet_pb2.RunWorkflowRequest(
            workflow=workflow, yamlContent=yaml_content or ""
        )

        # Add workflow files if provided
        if workflow_files:
            for file_info in workflow_files:
                file_upload = joblet_pb2.FileUpload(
                    path=file_info.get("path", ""),
                    content=file_info.get("content", b""),
                    mode=file_info.get("mode", 0o644),
                    isDirectory=file_info.get("is_directory", False),
                )
                request.workflowFiles.append(file_upload)

        try:
            response = self.stub.RunWorkflow(request)
            return {"workflow_uuid": response.workflowUuid, "status": response.status}
        except grpc.RpcError as e:
            raise WorkflowNotFoundError(f"Failed to run workflow: {e.details()}")

    def get_workflow_status(self, workflow_uuid: str) -> Dict[str, Any]:
        """Get workflow status

        Args:
            workflow_uuid: Workflow UUID

        Returns:
            Workflow status dictionary
        """
        request = joblet_pb2.GetWorkflowStatusRequest(workflowUuid=workflow_uuid)

        try:
            response = self.stub.GetWorkflowStatus(request)
            workflow = response.workflow
            jobs = []

            for job in response.jobs:
                jobs.append(
                    {
                        "job_uuid": job.jobUuid,
                        "job_name": job.jobName,
                        "status": job.status,
                        "dependencies": list(job.dependencies),
                        "start_time": self._timestamp_to_datetime(job.startTime),
                        "end_time": self._timestamp_to_datetime(job.endTime),
                        "exit_code": job.exitCode,
                    }
                )

            return {
                "workflow": {
                    "uuid": workflow.uuid,
                    "workflow": workflow.workflow,
                    "status": workflow.status,
                    "total_jobs": workflow.totalJobs,
                    "completed_jobs": workflow.completedJobs,
                    "failed_jobs": workflow.failedJobs,
                    "canceled_jobs": workflow.canceledJobs,
                    "created_at": self._timestamp_to_datetime(workflow.createdAt),
                    "started_at": self._timestamp_to_datetime(workflow.startedAt),
                    "completed_at": self._timestamp_to_datetime(workflow.completedAt),
                    "yaml_content": workflow.yamlContent,
                },
                "jobs": jobs,
            }
        except grpc.RpcError as e:
            raise WorkflowNotFoundError(
                f"Workflow {workflow_uuid} not found: {e.details()}"
            )

    def list_workflows(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        """List workflows

        Args:
            include_completed: Whether to include completed workflows

        Returns:
            List of workflow dictionaries
        """
        request = joblet_pb2.ListWorkflowsRequest(includeCompleted=include_completed)

        try:
            response = self.stub.ListWorkflows(request)
            workflows = []

            for workflow in response.workflows:
                workflows.append(
                    {
                        "uuid": workflow.uuid,
                        "workflow": workflow.workflow,
                        "status": workflow.status,
                        "total_jobs": workflow.totalJobs,
                        "completed_jobs": workflow.completedJobs,
                        "failed_jobs": workflow.failedJobs,
                        "canceled_jobs": workflow.canceledJobs,
                        "created_at": self._timestamp_to_datetime(workflow.createdAt),
                        "started_at": self._timestamp_to_datetime(workflow.startedAt),
                        "completed_at": self._timestamp_to_datetime(
                            workflow.completedAt
                        ),
                    }
                )

            return workflows
        except grpc.RpcError as e:
            raise WorkflowNotFoundError(f"Failed to list workflows: {e.details()}")

    def get_workflow_jobs(self, workflow_uuid: str) -> List[Dict[str, Any]]:
        """Get workflow jobs

        Args:
            workflow_uuid: Workflow UUID

        Returns:
            List of job dictionaries
        """
        request = joblet_pb2.GetWorkflowJobsRequest(workflowUuid=workflow_uuid)

        try:
            response = self.stub.GetWorkflowJobs(request)
            jobs = []

            for job in response.jobs:
                jobs.append(
                    {
                        "job_uuid": job.jobUuid,
                        "job_name": job.jobName,
                        "status": job.status,
                        "dependencies": list(job.dependencies),
                        "start_time": self._timestamp_to_datetime(job.startTime),
                        "end_time": self._timestamp_to_datetime(job.endTime),
                        "exit_code": job.exitCode,
                    }
                )

            return jobs
        except grpc.RpcError as e:
            raise WorkflowNotFoundError(
                f"Failed to get jobs for workflow {workflow_uuid}: {e.details()}"
            )

    def query_logs(
        self,
        job_id: str,
        stream: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 0,
        offset: int = 0,
    ) -> Iterator[Dict[str, Any]]:
        """Query historical logs for a job from persistent storage.

        This method delegates to the persist service. All queries go through
        the JobletService (port 50051), which internally proxies requests
        to joblet-persist via Unix socket IPC.

        Args:
            job_id: Job UUID
            stream: Stream filter ("stdout", "stderr", or None for both)
            start_time: Start time in Unix nanoseconds
            end_time: End time in Unix nanoseconds
            limit: Maximum lines to return (0 = all)
            offset: Skip lines

        Returns:
            Iterator yielding log line dictionaries

        Example:
            >>> for log in client.jobs.query_logs(job_id="abc123"):
            ...     timestamp = datetime.fromtimestamp(log['timestamp'] / 1e9)
            ...     content = log['content'].decode('utf-8')
            ...     print(f"[{timestamp}] {content}")
        """
        persist = self._persist_service
        if persist is None:
            raise RuntimeError("Persist service not available")
        return cast(
            Iterator[Dict[str, Any]],
            persist.query_logs(
                job_id=job_id,
                stream=stream,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                offset=offset,
            ),
        )

    def query_metrics(
        self,
        job_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 0,
        offset: int = 0,
    ) -> Iterator[Dict[str, Any]]:
        """Query historical metrics for a job from persistent storage.

        This method delegates to the persist service. All queries go through
        the JobletService (port 50051), which internally proxies requests
        to joblet-persist via Unix socket IPC.

        Args:
            job_id: Job UUID
            start_time: Start time in Unix nanoseconds
            end_time: End time in Unix nanoseconds
            limit: Maximum samples to return (0 = all)
            offset: Skip samples

        Returns:
            Iterator yielding metric dictionaries with CPU, memory, GPU, disk,
            and network data

        Example:
            >>> for metric in client.jobs.query_metrics(job_id="abc123"):
            ...     cpu = metric['data'].get('cpu_usage', 0)
            ...     memory_mb = metric['data'].get('memory_usage', 0) / (1024 * 1024)
            ...     print(f"CPU: {cpu:.2f}%, Memory: {memory_mb:.2f} MB")
        """
        persist = self._persist_service
        if persist is None:
            raise RuntimeError("Persist service not available")
        return cast(
            Iterator[Dict[str, Any]],
            persist.query_metrics(
                job_id=job_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                offset=offset,
            ),
        )

    @staticmethod
    def _timestamp_to_datetime(timestamp: Any) -> Optional[datetime]:
        """Convert protobuf timestamp to datetime"""
        if timestamp and timestamp.seconds:
            return datetime.fromtimestamp(timestamp.seconds + timestamp.nanos / 1e9)
        return None


class NetworkService:
    """Service for managing networks"""

    def __init__(self, channel: grpc.Channel):
        self.stub = joblet_pb2_grpc.NetworkServiceStub(channel)

    def create_network(self, name: str, cidr: str) -> Dict[str, Any]:
        """Create a new network

        Args:
            name: Network name
            cidr: CIDR block (e.g., "10.0.0.0/24")

        Returns:
            Network creation response
        """
        request = joblet_pb2.CreateNetworkReq(name=name, cidr=cidr)

        try:
            response = self.stub.CreateNetwork(request)
            return {
                "name": response.name,
                "cidr": response.cidr,
                "bridge": response.bridge,
            }
        except grpc.RpcError as e:
            raise NetworkError(f"Failed to create network: {e.details()}")

    def list_networks(self) -> List[Dict[str, Any]]:
        """List all networks

        Returns:
            List of network dictionaries
        """
        request = joblet_pb2.EmptyRequest()

        try:
            response = self.stub.ListNetworks(request)
            networks = []
            for network in response.networks:
                networks.append(
                    {
                        "name": network.name,
                        "cidr": network.cidr,
                        "bridge": network.bridge,
                        "job_count": network.jobCount,
                    }
                )
            return networks
        except grpc.RpcError as e:
            raise NetworkError(f"Failed to list networks: {e.details()}")

    def remove_network(self, name: str) -> Dict[str, Any]:
        """Remove a network

        Args:
            name: Network name

        Returns:
            Removal response
        """
        request = joblet_pb2.RemoveNetworkReq(name=name)

        try:
            response = self.stub.RemoveNetwork(request)
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            raise NetworkError(f"Failed to remove network: {e.details()}")


class VolumeService:
    """Service for managing volumes"""

    def __init__(self, channel: grpc.Channel):
        self.stub = joblet_pb2_grpc.VolumeServiceStub(channel)

    def create_volume(
        self, name: str, size: str, volume_type: str = "filesystem"
    ) -> Dict[str, Any]:
        """Create a new volume

        Args:
            name: Volume name
            size: Volume size (e.g., "1GB", "500MB")
            volume_type: Type of volume ("filesystem" or "memory")

        Returns:
            Volume creation response
        """
        request = joblet_pb2.CreateVolumeReq(name=name, size=size, type=volume_type)

        try:
            response = self.stub.CreateVolume(request)
            return {
                "name": response.name,
                "size": response.size,
                "type": response.type,
                "path": response.path,
            }
        except grpc.RpcError as e:
            raise VolumeError(f"Failed to create volume: {e.details()}")

    def list_volumes(self) -> List[Dict[str, Any]]:
        """List all volumes

        Returns:
            List of volume dictionaries
        """
        request = joblet_pb2.EmptyRequest()

        try:
            response = self.stub.ListVolumes(request)
            volumes = []
            for volume in response.volumes:
                volumes.append(
                    {
                        "name": volume.name,
                        "size": volume.size,
                        "type": volume.type,
                        "path": volume.path,
                        "created_time": volume.createdTime,
                        "job_count": volume.jobCount,
                    }
                )
            return volumes
        except grpc.RpcError as e:
            raise VolumeError(f"Failed to list volumes: {e.details()}")

    def remove_volume(self, name: str) -> Dict[str, Any]:
        """Remove a volume

        Args:
            name: Volume name

        Returns:
            Removal response
        """
        request = joblet_pb2.RemoveVolumeReq(name=name)

        try:
            response = self.stub.RemoveVolume(request)
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            raise VolumeError(f"Failed to remove volume: {e.details()}")


class MonitoringService:
    """Service for system monitoring"""

    def __init__(self, channel: grpc.Channel):
        self.stub = joblet_pb2_grpc.MonitoringServiceStub(channel)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status and resource availability

        Retrieves current system health information including CPU, memory,
        disk, network, and GPU metrics. Useful for monitoring server
        capacity before submitting resource-intensive jobs.

        Returns:
            Dict[str, Any]: System status containing:
                - available: Boolean indicating server availability
                - cpu: CPU metrics (usage, cores, load average)
                - memory: Memory usage and availability
                - disks: Disk usage per mount point
                - networks: Network interface statistics
                - host: Server information (hostname, OS, uptime)
                - gpu: GPU information (if available)

        Raises:
            RuntimeError: If unable to retrieve system status

        Example:
            >>> status = client.monitoring.get_system_status()
            >>> print(f"Available: {status['available']}")
            >>> print(f"CPU: {status['cpu']['usage_percent']:.1f}%")
            >>> print(f"Memory: {status['memory']['usage_percent']:.1f}%")
        """
        request = joblet_pb2.EmptyRequest()

        try:
            response = self.stub.GetSystemStatus(request)
            return self._parse_system_status(response)
        except grpc.RpcError as e:
            raise RuntimeError(f"Failed to get system status: {e.details()}")

    def stream_system_metrics(
        self, interval_seconds: int = 5, metric_types: Optional[List[str]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Stream real-time system metrics at regular intervals

        Continuously streams system performance metrics, useful for
        monitoring server health over time or building dashboards.

        Args:
            interval_seconds: Update interval in seconds (default: 5)
            metric_types: Optional list to filter specific metric types

        Yields:
            Dict[str, Any]: Metrics snapshot containing CPU, memory, disk,
                network, and process information at each interval

        Raises:
            RuntimeError: If unable to stream metrics

        Example:
            >>> metrics_stream = client.monitoring.stream_system_metrics(
            ...     interval_seconds=10
            ... )
            >>> for metrics in metrics_stream:
            ...     cpu = metrics['cpu']['usage_percent']
            ...     mem = metrics['memory']['usage_percent']
            ...     print(f"CPU: {cpu:.1f}%, Memory: {mem:.1f}%")
            ...     if cpu > 90:
            ...         break  # Stop monitoring if CPU too high
        """
        request = joblet_pb2.StreamMetricsReq(
            intervalSeconds=interval_seconds, metricTypes=metric_types or []
        )

        try:
            for metrics in self.stub.StreamSystemMetrics(request):
                yield self._parse_system_metrics(metrics)
        except grpc.RpcError as e:
            raise RuntimeError(f"Failed to stream metrics: {e.details()}")

    def _parse_system_status(self, response) -> Dict[str, Any]:
        """Parse system status response"""
        result = {"timestamp": response.timestamp, "available": response.available}

        if response.HasField("host"):
            result["host"] = self._parse_host_info(response.host)
        if response.HasField("cpu"):
            result["cpu"] = self._parse_cpu_metrics(response.cpu)
        if response.HasField("memory"):
            result["memory"] = self._parse_memory_metrics(response.memory)
        if response.disks:
            result["disks"] = [self._parse_disk_metrics(d) for d in response.disks]
        if response.networks:
            result["networks"] = [
                self._parse_network_metrics(n) for n in response.networks
            ]
        if response.HasField("io"):
            result["io"] = self._parse_io_metrics(response.io)
        if response.HasField("processes"):
            result["processes"] = self._parse_process_metrics(response.processes)
        if response.HasField("cloud"):
            result["cloud"] = self._parse_cloud_info(response.cloud)
        if response.HasField("server_version"):
            result["server_version"] = self._parse_server_version(
                response.server_version
            )

        return result

    def _parse_system_metrics(self, response) -> Dict[str, Any]:
        """Parse system metrics response"""
        result = {"timestamp": response.timestamp}

        if response.HasField("host"):
            result["host"] = self._parse_host_info(response.host)
        if response.HasField("cpu"):
            result["cpu"] = self._parse_cpu_metrics(response.cpu)
        if response.HasField("memory"):
            result["memory"] = self._parse_memory_metrics(response.memory)
        if response.disks:
            result["disks"] = [self._parse_disk_metrics(d) for d in response.disks]
        if response.networks:
            result["networks"] = [
                self._parse_network_metrics(n) for n in response.networks
            ]
        if response.HasField("io"):
            result["io"] = self._parse_io_metrics(response.io)
        if response.HasField("processes"):
            result["processes"] = self._parse_process_metrics(response.processes)
        if response.HasField("cloud"):
            result["cloud"] = self._parse_cloud_info(response.cloud)

        return result

    @staticmethod
    def _parse_host_info(host) -> Dict[str, Any]:
        """Parse host info"""
        return {
            "hostname": host.hostname,
            "os": host.os,
            "platform": host.platform,
            "platform_family": host.platformFamily,
            "platform_version": host.platformVersion,
            "kernel_version": host.kernelVersion,
            "kernel_arch": host.kernelArch,
            "architecture": host.architecture,
            "cpu_count": host.cpuCount,
            "total_memory": host.totalMemory,
            "boot_time": host.bootTime,
            "uptime": host.uptime,
            "node_id": host.nodeId,
            "server_ips": list(host.serverIPs),
            "mac_addresses": list(host.macAddresses),
        }

    @staticmethod
    def _parse_cpu_metrics(cpu) -> Dict[str, Any]:
        """Parse CPU metrics"""
        return {
            "cores": cpu.cores,
            "usage_percent": cpu.usagePercent,
            "user_time": cpu.userTime,
            "system_time": cpu.systemTime,
            "idle_time": cpu.idleTime,
            "io_wait_time": cpu.ioWaitTime,
            "steal_time": cpu.stealTime,
            "load_average": list(cpu.loadAverage),
            "per_core_usage": list(cpu.perCoreUsage),
        }

    @staticmethod
    def _parse_memory_metrics(memory) -> Dict[str, Any]:
        """Parse memory metrics"""
        return {
            "total_bytes": memory.totalBytes,
            "used_bytes": memory.usedBytes,
            "free_bytes": memory.freeBytes,
            "available_bytes": memory.availableBytes,
            "usage_percent": memory.usagePercent,
            "cached_bytes": memory.cachedBytes,
            "buffered_bytes": memory.bufferedBytes,
            "swap_total": memory.swapTotal,
            "swap_used": memory.swapUsed,
            "swap_free": memory.swapFree,
        }

    @staticmethod
    def _parse_disk_metrics(disk) -> Dict[str, Any]:
        """Parse disk metrics"""
        return {
            "device": disk.device,
            "mount_point": disk.mountPoint,
            "filesystem": disk.filesystem,
            "total_bytes": disk.totalBytes,
            "used_bytes": disk.usedBytes,
            "free_bytes": disk.freeBytes,
            "usage_percent": disk.usagePercent,
            "inodes_total": disk.inodesTotal,
            "inodes_used": disk.inodesUsed,
            "inodes_free": disk.inodesFree,
            "inodes_usage_percent": disk.inodesUsagePercent,
        }

    @staticmethod
    def _parse_network_metrics(network) -> Dict[str, Any]:
        """Parse network metrics"""
        return {
            "interface": network.interface,
            "bytes_received": network.bytesReceived,
            "bytes_sent": network.bytesSent,
            "packets_received": network.packetsReceived,
            "packets_sent": network.packetsSent,
            "errors_in": network.errorsIn,
            "errors_out": network.errorsOut,
            "drops_in": network.dropsIn,
            "drops_out": network.dropsOut,
            "receive_rate": network.receiveRate,
            "transmit_rate": network.transmitRate,
        }

    @staticmethod
    def _parse_io_metrics(io) -> Dict[str, Any]:
        """Parse IO metrics"""
        result = {
            "total_reads": io.totalReads,
            "total_writes": io.totalWrites,
            "read_bytes": io.readBytes,
            "write_bytes": io.writeBytes,
            "read_rate": io.readRate,
            "write_rate": io.writeRate,
        }

        if io.diskIO:
            result["disk_io"] = []
            for disk_io in io.diskIO:
                result["disk_io"].append(
                    {
                        "device": disk_io.device,
                        "reads_completed": disk_io.readsCompleted,
                        "writes_completed": disk_io.writesCompleted,
                        "read_bytes": disk_io.readBytes,
                        "write_bytes": disk_io.writeBytes,
                        "read_time": disk_io.readTime,
                        "write_time": disk_io.writeTime,
                        "io_time": disk_io.ioTime,
                        "utilization": disk_io.utilization,
                    }
                )

        return result

    @staticmethod
    def _parse_process_metrics(processes) -> Dict[str, Any]:
        """Parse process metrics"""
        result = {
            "total_processes": processes.totalProcesses,
            "running_processes": processes.runningProcesses,
            "sleeping_processes": processes.sleepingProcesses,
            "stopped_processes": processes.stoppedProcesses,
            "zombie_processes": processes.zombieProcesses,
            "total_threads": processes.totalThreads,
        }

        if processes.topByCPU:
            result["top_by_cpu"] = []
            for proc in processes.topByCPU:
                result["top_by_cpu"].append(
                    {
                        "pid": proc.pid,
                        "ppid": proc.ppid,
                        "name": proc.name,
                        "command": proc.command,
                        "cpu_percent": proc.cpuPercent,
                        "memory_percent": proc.memoryPercent,
                        "memory_bytes": proc.memoryBytes,
                        "status": proc.status,
                        "start_time": proc.startTime,
                        "user": proc.user,
                    }
                )

        if processes.topByMemory:
            result["top_by_memory"] = []
            for proc in processes.topByMemory:
                result["top_by_memory"].append(
                    {
                        "pid": proc.pid,
                        "ppid": proc.ppid,
                        "name": proc.name,
                        "command": proc.command,
                        "cpu_percent": proc.cpuPercent,
                        "memory_percent": proc.memoryPercent,
                        "memory_bytes": proc.memoryBytes,
                        "status": proc.status,
                        "start_time": proc.startTime,
                        "user": proc.user,
                    }
                )

        return result

    @staticmethod
    def _parse_cloud_info(cloud) -> Dict[str, Any]:
        """Parse cloud info"""
        return {
            "provider": cloud.provider,
            "region": cloud.region,
            "zone": cloud.zone,
            "instance_id": cloud.instanceID,
            "instance_type": cloud.instanceType,
            "hypervisor_type": cloud.hypervisorType,
            "metadata": dict(cloud.metadata),
        }

    @staticmethod
    def _parse_server_version(version) -> Dict[str, Any]:
        """Parse server version info"""
        return {
            "version": version.version,
            "git_commit": version.git_commit,
            "git_tag": version.git_tag,
            "build_date": version.build_date,
            "component": version.component,
            "go_version": version.go_version,
            "platform": version.platform,
            "proto_commit": version.proto_commit,
            "proto_tag": version.proto_tag,
        }


class RuntimeService:
    """Service for managing runtimes"""

    def __init__(self, channel: grpc.Channel):
        self.stub = joblet_pb2_grpc.RuntimeServiceStub(channel)

    def list_runtimes(self) -> List[Dict[str, Any]]:
        """List all available runtimes

        Returns:
            List of runtime dictionaries
        """
        request = joblet_pb2.EmptyRequest()

        try:
            response = self.stub.ListRuntimes(request)
            runtimes = []
            for runtime in response.runtimes:
                runtime_dict = {
                    "name": runtime.name,
                    "language": runtime.language,
                    "version": runtime.version,
                    "description": runtime.description,
                    "size_bytes": runtime.sizeBytes,
                    "packages": list(runtime.packages),
                    "available": runtime.available,
                }

                if runtime.HasField("requirements"):
                    runtime_dict["requirements"] = {
                        "architectures": list(runtime.requirements.architectures),
                        "gpu": runtime.requirements.gpu,
                    }

                runtimes.append(runtime_dict)

            return runtimes
        except grpc.RpcError as e:
            raise RuntimeNotFoundError(f"Failed to list runtimes: {e.details()}")

    def get_runtime_info(self, runtime: str) -> Dict[str, Any]:
        """Get runtime information

        Args:
            runtime: Runtime specification

        Returns:
            Runtime information dictionary
        """
        request = joblet_pb2.RuntimeInfoReq(runtime=runtime)

        try:
            response = self.stub.GetRuntimeInfo(request)
            if not response.found:
                raise RuntimeNotFoundError(f"Runtime {runtime} not found")

            runtime_info = {
                "name": response.runtime.name,
                "language": response.runtime.language,
                "version": response.runtime.version,
                "description": response.runtime.description,
                "size_bytes": response.runtime.sizeBytes,
                "packages": list(response.runtime.packages),
                "available": response.runtime.available,
            }

            if response.runtime.HasField("requirements"):
                runtime_info["requirements"] = {
                    "architectures": list(response.runtime.requirements.architectures),
                    "gpu": response.runtime.requirements.gpu,
                }

            return runtime_info
        except grpc.RpcError as e:
            raise RuntimeNotFoundError(f"Failed to get runtime info: {e.details()}")

    def test_runtime(self, runtime: str) -> Dict[str, Any]:
        """Test a runtime

        Args:
            runtime: Runtime specification

        Returns:
            Test result dictionary
        """
        request = joblet_pb2.RuntimeTestReq(runtime=runtime)

        try:
            response = self.stub.TestRuntime(request)
            return {
                "success": response.success,
                "output": response.output,
                "error": response.error,
                "exit_code": response.exitCode,
            }
        except grpc.RpcError as e:
            raise RuntimeNotFoundError(f"Failed to test runtime: {e.details()}")

    def install_runtime_from_github(
        self,
        runtime_spec: str,
        repository: str,
        branch: Optional[str] = None,
        path: Optional[str] = None,
        force_reinstall: bool = False,
        stream: bool = False,
    ):
        """Install runtime from GitHub repository

        Args:
            runtime_spec: Runtime specification
            repository: GitHub repository
            branch: Optional branch
            path: Optional path in repository
            force_reinstall: Force reinstallation
            stream: Stream installation progress

        Returns:
            Installation response or stream iterator
        """
        request = joblet_pb2.InstallRuntimeRequest(
            runtimeSpec=runtime_spec,
            repository=repository,
            branch=branch or "",
            path=path or "",
            forceReinstall=force_reinstall,
        )

        try:
            if stream:
                return self._stream_runtime_installation(
                    self.stub.StreamingInstallRuntimeFromGithub(request)
                )
            else:
                response = self.stub.InstallRuntimeFromGithub(request)
                return {
                    "build_job_uuid": response.buildJobUuid,
                    "runtime_spec": response.runtimeSpec,
                    "status": response.status,
                    "message": response.message,
                    "repository": response.repository,
                    "resolved_path": response.resolvedPath,
                }
        except grpc.RpcError as e:
            raise RuntimeError(f"Failed to install runtime: {e.details()}")

    def install_runtime_from_local(
        self,
        runtime_spec: str,
        files: List[Dict[str, Any]],
        force_reinstall: bool = False,
        stream: bool = False,
    ):
        """Install runtime from local files

        Args:
            runtime_spec: Runtime specification
            files: List of file dictionaries
            force_reinstall: Force reinstallation
            stream: Stream installation progress

        Returns:
            Installation response or stream iterator
        """
        request = joblet_pb2.InstallRuntimeFromLocalRequest(
            runtimeSpec=runtime_spec, forceReinstall=force_reinstall
        )

        for file_info in files:
            runtime_file = joblet_pb2.RuntimeFile(
                path=file_info.get("path", ""),
                content=file_info.get("content", b""),
                executable=file_info.get("executable", False),
            )
            request.files.append(runtime_file)

        try:
            if stream:
                return self._stream_runtime_installation(
                    self.stub.StreamingInstallRuntimeFromLocal(request)
                )
            else:
                response = self.stub.InstallRuntimeFromLocal(request)
                return {
                    "build_job_uuid": response.buildJobUuid,
                    "runtime_spec": response.runtimeSpec,
                    "status": response.status,
                    "message": response.message,
                }
        except grpc.RpcError as e:
            raise RuntimeError(f"Failed to install runtime: {e.details()}")

    def _stream_runtime_installation(self, stream_response):
        """Stream runtime installation progress"""
        for chunk in stream_response:
            if chunk.HasField("progress"):
                progress = chunk.progress
                yield {
                    "type": "progress",
                    "message": progress.message,
                    "step": progress.step,
                    "total_steps": progress.total_steps,
                }
            elif chunk.HasField("log"):
                log = chunk.log
                yield {"type": "log", "data": log.data}
            elif chunk.HasField("result"):
                result = chunk.result
                yield {
                    "type": "result",
                    "success": result.success,
                    "message": result.message,
                    "runtime_spec": result.runtime_spec,
                    "install_path": result.install_path,
                }

    def validate_runtime_spec(self, runtime_spec: str) -> Dict[str, Any]:
        """Validate runtime specification

        Args:
            runtime_spec: Runtime specification to validate

        Returns:
            Validation result dictionary
        """
        request = joblet_pb2.ValidateRuntimeSpecRequest(runtimeSpec=runtime_spec)

        try:
            response = self.stub.ValidateRuntimeSpec(request)
            result = {
                "valid": response.valid,
                "message": response.message,
                "normalized_spec": response.normalizedSpec,
            }

            if response.HasField("specInfo"):
                result["spec_info"] = {
                    "language": response.specInfo.language,
                    "version": response.specInfo.version,
                    "variants": list(response.specInfo.variants),
                    "architecture": response.specInfo.architecture,
                }

            return result
        except grpc.RpcError as e:
            raise ValidationError(f"Failed to validate runtime spec: {e.details()}")

    def remove_runtime(self, runtime: str) -> Dict[str, Any]:
        """Remove a runtime

        Args:
            runtime: Runtime to remove

        Returns:
            Removal response dictionary
        """
        request = joblet_pb2.RuntimeRemoveReq(runtime=runtime)

        try:
            response = self.stub.RemoveRuntime(request)
            return {
                "success": response.success,
                "message": response.message,
                "freed_space_bytes": response.freedSpaceBytes,
            }
        except grpc.RpcError as e:
            raise RuntimeNotFoundError(f"Failed to remove runtime: {e.details()}")


class PersistService:
    """Service for querying historical logs and metrics (Port 50052)"""

    def __init__(self, channel: grpc.Channel):
        self.stub = persist_pb2_grpc.PersistServiceStub(channel)

    def query_logs(
        self,
        job_id: str,
        stream: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 0,
        offset: int = 0,
    ) -> Iterator[Dict[str, Any]]:
        """Query historical logs for a job

        Args:
            job_id: Job UUID
            stream: Stream filter ("stdout", "stderr", or None for both)
            start_time: Start time in Unix nanoseconds
            end_time: End time in Unix nanoseconds
            limit: Maximum lines to return (0 = all)
            offset: Skip lines

        Yields:
            Log line dictionaries with job_id, stream, timestamp, sequence, content
        """
        # Convert stream string to enum
        stream_type = persist_pb2.STREAM_TYPE_UNSPECIFIED
        if stream == "stdout":
            stream_type = persist_pb2.STREAM_TYPE_STDOUT
        elif stream == "stderr":
            stream_type = persist_pb2.STREAM_TYPE_STDERR

        request = persist_pb2.QueryLogsRequest(
            job_id=job_id,
            stream=stream_type,
            start_time=start_time or 0,
            end_time=end_time or 0,
            limit=limit,
            offset=offset,
        )

        try:
            for log_line in self.stub.QueryLogs(request):
                # Convert stream enum to string
                stream_str = "unknown"
                if log_line.stream == persist_pb2.STREAM_TYPE_STDOUT:
                    stream_str = "stdout"
                elif log_line.stream == persist_pb2.STREAM_TYPE_STDERR:
                    stream_str = "stderr"

                yield {
                    "job_id": log_line.job_id,
                    "stream": stream_str,
                    "timestamp": log_line.timestamp,
                    "sequence": log_line.sequence,
                    "content": log_line.content,
                }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to query logs: {e.details()}")

    def query_metrics(
        self,
        job_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 0,
        offset: int = 0,
    ) -> Iterator[Dict[str, Any]]:
        """Query historical metrics for a job

        Args:
            job_id: Job UUID
            start_time: Start time in Unix nanoseconds
            end_time: End time in Unix nanoseconds
            limit: Maximum samples to return (0 = all)
            offset: Skip samples

        Yields:
            Metric dictionaries with job_id, timestamp, sequence, and data
        """
        request = persist_pb2.QueryMetricsRequest(
            job_id=job_id,
            start_time=start_time or 0,
            end_time=end_time or 0,
            limit=limit,
            offset=offset,
        )

        try:
            for metric in self.stub.QueryMetrics(request):
                metric_dict = {
                    "job_id": metric.job_id,
                    "timestamp": metric.timestamp,
                    "sequence": metric.sequence,
                    "data": {},
                }

                if metric.HasField("data"):
                    metric_dict["data"] = {
                        "cpu_usage": metric.data.cpu_usage,
                        "memory_usage": metric.data.memory_usage,
                        "gpu_usage": metric.data.gpu_usage,
                    }

                    if metric.data.HasField("disk_io"):
                        metric_dict["data"]["disk_io"] = {
                            "read_bytes": metric.data.disk_io.read_bytes,
                            "write_bytes": metric.data.disk_io.write_bytes,
                            "read_ops": metric.data.disk_io.read_ops,
                            "write_ops": metric.data.disk_io.write_ops,
                        }

                    if metric.data.HasField("network_io"):
                        metric_dict["data"]["network_io"] = {
                            "rx_bytes": metric.data.network_io.rx_bytes,
                            "tx_bytes": metric.data.network_io.tx_bytes,
                            "rx_packets": metric.data.network_io.rx_packets,
                            "tx_packets": metric.data.network_io.tx_packets,
                        }

                yield metric_dict
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to query metrics: {e.details()}")


__all__ = [
    "JobService",
    "NetworkService",
    "VolumeService",
    "MonitoringService",
    "RuntimeService",
    "PersistService",
]
