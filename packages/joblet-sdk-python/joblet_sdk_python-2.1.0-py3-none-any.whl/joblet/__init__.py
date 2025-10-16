"""
Joblet Python SDK

A comprehensive Python SDK for interacting with the Joblet job orchestration system.
This SDK provides a high-level, Pythonic interface to all Joblet functionality including
job execution, workflow management, runtime environments, networking, storage, and
system monitoring.

Key Features:
    - Simple job execution with resource constraints
    - Complex multi-job workflow orchestration
    - Runtime environment management and installation
    - Virtual network and persistent volume management
    - Real-time system monitoring and metrics streaming
    - Comprehensive error handling with specific exception types
    - Full type hints for better development experience

Quick Start:
    >>> from joblet import JobletClient
    >>>
    >>> # Connect to local Joblet server
    >>> with JobletClient() as client:
    ...     # Check server health
    ...     if client.health_check():
    ...         # Run a simple job
    ...         job = client.jobs.run_job(
    ...             command="echo",
    ...             args=["Hello, Joblet!"],
    ...             name="greeting-job"
    ...         )
    ...         print(f"Job started: {job['job_uuid']}")
    ...
    ...         # Monitor job status
    ...         status = client.jobs.get_job_status(job['job_uuid'])
    ...         print(f"Status: {status['status']}")

For more examples and detailed documentation, see:
    - examples/ directory for usage examples
    - API_REFERENCE.md for complete API documentation
    - README.md for setup and configuration guide

Repository: https://github.com/ehsaniara/joblet-proto
"""

__version__ = "2.1.0"
__author__ = "Jay Ehsaniara"
__license__ = "MIT"

# Main client class - the primary entry point
from .client import JobletClient

# Exception classes - for proper error handling
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    JobletException,
    JobNotFoundError,
    NetworkError,
    RuntimeNotFoundError,
    TimeoutError,
    ValidationError,
    VolumeError,
    WorkflowNotFoundError,
)

# Service classes - accessed through client properties
from .services import (
    JobService,
    MonitoringService,
    NetworkService,
    RuntimeService,
    VolumeService,
)

# Public API - these classes/functions are available when importing the package
__all__ = [
    # Main client
    "JobletClient",
    # Service classes (though typically accessed via client properties)
    "JobService",
    "NetworkService",
    "VolumeService",
    "MonitoringService",
    "RuntimeService",
    # Exception hierarchy for error handling
    "JobletException",
    "ConnectionError",
    "AuthenticationError",
    "JobNotFoundError",
    "WorkflowNotFoundError",
    "RuntimeNotFoundError",
    "NetworkError",
    "VolumeError",
    "ValidationError",
    "TimeoutError",
]
