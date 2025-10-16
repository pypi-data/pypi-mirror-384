# Joblet Python SDK

The official Python SDK for [Joblet](https://github.com/ehsaniara/joblet) - a distributed job orchestration system with GPU support.

## Installation

```bash
pip install joblet-sdk-python
```

## Quick Start

```python
from joblet import JobletClient

# Connect to your Joblet server
with JobletClient(
    host="your-joblet-server.com",
    port=50051,
    ca_cert_path="ca.pem",
    client_cert_path="client.pem",
    client_key_path="client.key"
) as client:
    # Run a simple job
    job = client.jobs.run_job(
        command="echo",
        args=["Hello, Joblet!"],
        name="my-first-job"
    )
    print(f"Job started: {job['job_uuid']}")
```

## Configuration

Create `~/.rnx/rnx-config.yml`:

```yaml
version: "3.0"
nodes:
  default:
    address: "your-joblet-server:50051"  # Required - single endpoint for all operations
    nodeId: "node-001"  # Optional: unique identifier for this node
    cert: |
      -----BEGIN CERTIFICATE-----
      # Your client certificate
      -----END CERTIFICATE-----
    key: |
      -----BEGIN PRIVATE KEY-----
      # Your client private key
      -----END PRIVATE KEY-----
    ca: |
      -----BEGIN CERTIFICATE-----
      # Your CA certificate
      -----END CERTIFICATE-----
```

**Configuration Fields:**
- `address` - **Required**: Joblet service endpoint (default port 50051)
  - Single endpoint for all operations including historical queries
  - Joblet internally handles persistence via Unix socket IPC
- `nodeId` - Optional: Unique identifier for the node
- `cert` - **Required**: Client certificate for mTLS authentication
- `key` - **Required**: Client private key for mTLS authentication
- `ca` - **Required**: CA certificate for server verification

**Note**: Joblet runs as a unified Linux systemd service with embedded persistence (joblet-persist). All operations go through the main service on port 50051, which transparently handles both live streaming and historical queries. See the [Joblet Installation Guide](https://github.com/ehsaniara/joblet/blob/main/docs/INSTALLATION.md) for server setup.

## GPU Support

```python
# Run GPU-accelerated job
job = client.jobs.run_job(
    command="nvidia-smi",
    name="gpu-job",
    gpu_count=1,
    gpu_memory_mb=4096,
    runtime="python-3.11-ml"
)
```

## What You Can Do

### Run Jobs Anywhere

```python
# Run compute-intensive tasks on remote servers
job = client.jobs.run_job(
    command="python",
    args=["train_model.py"],
    max_cpu=800,  # 8 cores
    max_memory=16384,  # 16GB
    gpu_count=2
)
```

### Stream Logs in Real-Time

```python
# Get complete logs from any job (running or completed)
for chunk in client.jobs.get_job_logs(job['job_uuid']):
    print(chunk.decode('utf-8'), end='', flush=True)
```

### Query Historical Data

```python
# Analyze past job performance
for metric in client.persist.query_metrics(job_id=job_uuid):
    print(f"CPU: {metric['data']['cpu_usage']:.2f}%")
    print(f"Memory: {metric['data']['memory_usage'] / 1e9:.2f} GB")
```

### Build Workflows

```python
# Chain multiple jobs with dependencies
workflow = client.jobs.run_workflow(
    workflow="data-pipeline.yml",
    yaml_content="""
    jobs:
      preprocess:
        command: python preprocess.py
      train:
        command: python train.py
        depends_on: [preprocess]
      evaluate:
        command: python evaluate.py
        depends_on: [train]
    """
)
```

### Manage Resources

```python
# Create isolated networks and persistent storage
network = client.networks.create_network("ml-net", "10.0.1.0/24")
volume = client.volumes.create_volume("data", "100GB")

# Use in jobs
job = client.jobs.run_job(
    command="python",
    args=["process_data.py"],
    network="ml-net",
    volumes=["data:/data"]
)
```

### Monitor System Health

```python
# Get real-time system metrics
for metrics in client.monitoring.stream_system_metrics(interval_seconds=5):
    cpu = metrics['cpu']['usage_percent']
    memory = metrics['memory']['usage_percent']
    print(f"System: CPU {cpu:.1f}%, Memory {memory:.1f}%")
```

## API Reference

### Jobs
- `client.jobs.run_job()` - Execute a job
- `client.jobs.cancel_job()` - Cancel a scheduled job
- `client.jobs.stop_job()` - Stop a running job
- `client.jobs.get_job_status()` - Get job status
- `client.jobs.get_job_logs()` - **Smart log streaming** (historical + live)
- `client.jobs.stream_live_logs()` - Live-only log streaming
- `client.jobs.run_workflow()` - Execute a workflow

### Historical Data

- `client.persist.query_logs()` - Query historical logs with filtering
- `client.persist.query_metrics()` - Query historical metrics data

### Resources
- `client.networks` - Network management
- `client.volumes` - Storage management
- `client.monitoring` - System monitoring
- `client.runtimes` - Runtime environments

For complete API documentation, see [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

## Development

### Setup

```bash
# Clone and setup
git clone https://github.com/ehsaniara/joblet-sdk-python.git
cd joblet-sdk-python

# Install development dependencies (editable mode)
make dev

# Or manually:
pip install -e .[dev]
pre-commit install
```

### Testing

```bash
# Run tests with coverage
make test

# Run linting (exactly what CI runs)
make lint

# IMPORTANT: Test package installation before release (CI-like)
make test-package
```

### Why `make test-package` is Important

**Problem**: Editable installs (`pip install -e .`) can mask packaging issues. Your local tests may pass but CI/production installs may fail.

**Solution**: Before committing or releasing, run:
```bash
make test-package
```

This command:
1. Uninstalls the editable version
2. Builds a clean package
3. Installs it like CI and end-users will
4. Runs all tests against the installed package
5. Catches issues like missing `__init__.py`, incorrect package structure, etc.

After testing, restore editable install:
```bash
pip install -e .[dev]
```

### Other Commands

```bash
# Build distribution packages
make build

# Regenerate protobuf files
make proto

# Clean build artifacts
make clean
```

## Examples

See the `examples/` directory for more detailed usage examples:
- `01_basic_usage.py` - Simple job execution and management
- `02_advanced_features.py` - Resource limits, environment variables, GPU support
- `03_streaming_logs.py` - Real-time log streaming
- `04_historical_logs_metrics.py` - Query historical logs and metrics
- `05_smart_log_streaming.py` - Intelligent log streaming (historical + live)
- `06_long_running_job_demo.py` - Long-running job with complete log retrieval

For detailed documentation, see [examples/README.md](examples/README.md)

## Related Projects

- **[Joblet](https://github.com/ehsaniara/joblet)** - Main orchestration system (server-side)
- **[joblet-proto](https://github.com/ehsaniara/joblet-proto)** - Protocol Buffer definitions
- **rnx** - Official CLI tool (included in Joblet repo)

## License

MIT License - see LICENSE file for details.
