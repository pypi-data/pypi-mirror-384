# RunPodManager

**A Python library for seamless RunPod GPU pod management and workflow automation**

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![RunPod](https://img.shields.io/badge/RunPod-API-purple.svg)](https://www.runpod.io/)

RunPodManager simplifies the process of creating, managing, and executing workflows on RunPod GPU pods. Whether you're training machine learning models, running experiments, or need remote GPU compute, RunPodManager provides an intuitive Python interface to handle everything from pod provisioning to SSH operations and port forwarding.

## Features

- **Complete Pod Lifecycle Management**: Create, connect, stop, resume, and terminate pods programmatically
- **Bidirectional Data Transfer**: Upload and download files and directories between local machine and pods via SCP
- **Remote Command Execution**: Run commands on pods with real-time output streaming
- **SSH Port Forwarding**: Forward ports for services like Jupyter, TensorBoard, or web applications
- **Background Process Management**: Launch long-running processes with automatic port forwarding
- **Smart Pod State Checking**: Verify pod existence and running status before operations
- **Flexible Configuration**: Support for custom Docker images, GPU types, volumes, and environment variables

## Installation

```bash
pip install runpodmanager
```

## Quick Start

```python
from runpodmanager import RunPodManager
import os

# Initialize with your RunPod API key
manager = RunPodManager(api_key=os.getenv("RUNPOD_API_KEY"))

# Create a pod
pod_config = {
    "name": "my-gpu-pod",
    "image_name": "runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04",
    "gpu_type_id": "NVIDIA RTX 2000 Ada Generation",
    "gpu_count": 1,
    "cloud_type": "ALL",
    "support_public_ip": True,
    "start_ssh": True,
}

manager.create_pod(pod_config)

# Wait for pod to be ready
import time
while not manager.is_pod_running():
    print("Waiting for pod to start...")
    time.sleep(5)

# Execute a command
manager.execute_command("nvidia-smi")

# Terminate when done
manager.terminate_pod()
```

## Usage Guide

### Initialization

You can provide your RunPod API key in two ways:

```python
# Option 1: Pass directly
manager = RunPodManager(api_key="your-api-key")

# Option 2: Set environment variable RUNPOD_API_KEY
manager = RunPodManager()
```

### Creating a Pod

Create a fully configured pod with custom settings:

```python
pod_config = {
    "name": "training-pod",
    "image_name": "runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04",
    "gpu_type_id": "NVIDIA RTX 2000 Ada Generation",
    "gpu_count": 1,
    "cloud_type": "ALL",  # Options: "ALL", "SECURE", "COMMUNITY"
    "support_public_ip": True,
    "start_ssh": True,
    "volume_in_gb": 50,
    "container_disk_in_gb": 50,
    "min_vcpu_count": 1,
    "docker_args": "",
    "ports": "8888/http,6006/http,22/tcp",
    "env": {
        "HUGGINGFACE_TOKEN": os.getenv("HUGGINGFACE_TOKEN"),
        "WANDB_API_KEY": os.getenv("WANDB_API_KEY"),
    }
}

manager.create_pod(pod_config)
```

### Connecting to an Existing Pod

```python
# Connect to a pod you created previously
manager.connect_to_pod(pod_id="your-pod-id")

# Check if pod is running
if manager.is_pod_running():
    print("Pod is ready!")
```

### Pod Lifecycle Management

```python
# Stop a running pod (saves costs when not in use)
manager.stop_pod()

# Resume a stopped pod
manager.resume_pod()

# Terminate a pod permanently
manager.terminate_pod()

# Check pod status
if manager.pod_exists():
    print("Pod exists")

if manager.is_pod_running():
    print("Pod is running")
```

### Transferring Data to Pod

Upload local files or directories to your pod:

```python
# Transfer a single file
manager.transfer_data_to_pod(
    local_path="./model.py",
    remote_path="/workspace/"
)

# Transfer a directory recursively
manager.transfer_data_to_pod(
    local_path="./dataset/",
    remote_path="/workspace/data/"
)

# Transfer to home directory
manager.transfer_data_to_pod(
    local_path="./training_script.py",
    remote_path=""  # Defaults to home directory
)
```

### Downloading Data from Pod

Download files or directories from your pod to your local machine:

```python
# Download a single file
manager.download_data_from_pod(
    remote_path="/workspace/model.pth",
    local_path="./models/"
)

# Download a directory recursively
manager.download_data_from_pod(
    remote_path="/workspace/results/",
    local_path="./local_results/"
)

# Download to current directory
manager.download_data_from_pod(
    remote_path="/workspace/logs/training.log",
    local_path="."  # Defaults to current directory
)

# Download training outputs
manager.download_data_from_pod(
    remote_path="runs",  # TensorBoard logs
    local_path="./tensorboard_logs/"
)
```

### Executing Commands

#### Foreground Execution (with real-time output)

```python
# Run a command and see output in real-time
manager.execute_command("pip install transformers accelerate")

# Execute a training script
manager.execute_command("python train.py --epochs 10 --batch-size 32")
```

#### Background Execution

```python
# Run a command in the background
manager.execute_command(
    command="python long_running_task.py",
    background=True
)
```

#### Background Execution with Port Forwarding

Perfect for Jupyter, TensorBoard, or web applications:

```python
# Start TensorBoard with port forwarding
tb_process = manager.execute_command(
    command="tensorboard --logdir=runs --port=6006 --bind_all",
    background=True,
    port_forward=(6006, 6006)  # (local_port, remote_port)
)

# Now access TensorBoard at http://localhost:6006
print("TensorBoard running at http://localhost:6006")
```

## Complete Workflow Example

Here's a complete example that demonstrates a typical machine learning workflow:

```python
from runpodmanager import RunPodManager
import time
import os

# Initialize
manager = RunPodManager()

# Create a pod with TensorBoard port exposed
pod_config = {
    "name": "ml-training-pod",
    "image_name": "runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04",
    "gpu_type_id": "NVIDIA RTX 2000 Ada Generation",
    "gpu_count": 1,
    "cloud_type": "ALL",
    "support_public_ip": True,
    "start_ssh": True,
    "volume_in_gb": 50,
    "container_disk_in_gb": 50,
    "ports": "6006/http,22/tcp",
}

print("Creating pod...")
manager.create_pod(pod_config)

# Wait for pod to be ready
print("Waiting for pod to start...")
while not manager.is_pod_running():
    time.sleep(5)
print("Pod is running!")

# Transfer training script
print("Transferring training script...")
manager.transfer_data_to_pod(
    local_path="./train.py",
    remote_path="/workspace/"
)

# Install dependencies
print("Installing dependencies...")
manager.execute_command("pip install tensorboard torch torchvision")

# Start TensorBoard with port forwarding
print("Starting TensorBoard...")
tb_process = manager.execute_command(
    command="tensorboard --logdir=runs --port=6006 --bind_all",
    background=True,
    port_forward=(6006, 6006)
)
print("TensorBoard available at http://localhost:6006")

# Run training
print("Starting training...")
manager.execute_command("cd /workspace && python train.py")

# Download training results
print("Downloading training results...")
manager.download_data_from_pod(
    remote_path="runs",
    local_path="./training_results/"
)

# Training complete, terminate pod
print("Training complete! Terminating pod...")
manager.terminate_pod()
print("Done!")
```

## API Reference

### `RunPodManager(api_key: Optional[str] = None)`

Initialize the RunPodManager.

**Parameters:**
- `api_key` (str, optional): RunPod API key. If not provided, reads from `RUNPOD_API_KEY` environment variable.

**Raises:**
- `ValueError`: If API key is not provided and not found in environment variables.

---

### `create_pod(pod_config: dict) -> None`

Creates a new RunPod pod.

**Parameters:**
- `pod_config` (dict): Pod configuration dictionary. See Configuration Options below.

**Returns:** None (sets `self.pod_id`)

---

### `connect_to_pod(pod_id: str) -> None`

Connects to an existing pod.

**Parameters:**
- `pod_id` (str): The ID of the pod to connect to.

**Raises:**
- `ValueError`: If the pod does not exist.

---

### `stop_pod() -> None`

Stops the current pod (can be resumed later).

---

### `resume_pod() -> None`

Resumes a stopped pod with the same GPU configuration.

---

### `terminate_pod() -> None`

Permanently terminates the current pod.

---

### `pod_exists() -> bool`

Checks if the current pod exists.

**Returns:** `True` if pod exists, `False` otherwise.

---

### `is_pod_running() -> bool`

Checks if the current pod is running.

**Returns:** `True` if pod is running, `False` otherwise.

---

### `transfer_data_to_pod(local_path: str, remote_path: str = "") -> None`

Transfers local files or directories to the pod via SCP.

**Parameters:**
- `local_path` (str): Path to local file or directory.
- `remote_path` (str, optional): Destination path on pod. Defaults to home directory.

**Raises:**
- `ValueError`: If pod is not running.
- `Exception`: If transfer fails.

---

### `download_data_from_pod(remote_path: str, local_path: str = ".") -> None`

Downloads files or directories from the pod to local machine via SCP.

**Parameters:**
- `remote_path` (str): Path to file or directory on the pod.
- `local_path` (str, optional): Local destination path. Defaults to current directory.

**Raises:**
- `ValueError`: If pod is not running.
- `Exception`: If download fails.

---

### `execute_command(command: str, background: bool = False, port_forward: tuple[int, int] = None)`

Executes a command on the pod via SSH.

**Parameters:**
- `command` (str): Command to execute.
- `background` (bool, optional): If `True`, runs command in background. Default is `False`.
- `port_forward` (tuple[int, int], optional): Tuple of `(local_port, remote_port)` for SSH port forwarding.

**Returns:**
- `subprocess.Popen` object if `background=True` with `port_forward`
- Return code (int) otherwise

**Raises:**
- `ValueError`: If pod is not running.

## Configuration Options

The `pod_config` dictionary supports the following options:

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Name for your pod |
| `image_name` | str | Docker image (e.g., `runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04`) |
| `gpu_type_id` | str | GPU type (e.g., `NVIDIA RTX 2000 Ada Generation`, `NVIDIA A100 80GB PCIe`) |
| `gpu_count` | int | Number of GPUs |
| `cloud_type` | str | `"ALL"`, `"SECURE"`, or `"COMMUNITY"` |
| `support_public_ip` | bool | Enable public IP address |
| `start_ssh` | bool | Enable SSH access (required for RunPodManager operations) |
| `volume_in_gb` | int | Persistent volume size in GB |
| `container_disk_in_gb` | int | Container disk size in GB |
| `min_vcpu_count` | int | Minimum vCPU count |
| `docker_args` | str | Additional Docker arguments |
| `ports` | str | Port mappings (e.g., `"8888/http,6006/http,22/tcp"`) |
| `env` | dict | Environment variables |

## Best Practices

1. **Always Set SSH**: Ensure `start_ssh: True` in your pod configuration, as it's required for all RunPodManager operations.

2. **Wait for Pod Ready**: Always check `is_pod_running()` before executing commands or transferring data:
   ```python
   while not manager.is_pod_running():
       time.sleep(5)
   ```

3. **Use Environment Variables**: Store sensitive data like API keys in environment variables:
   ```python
   pod_config = {
       "env": {
           "API_KEY": os.getenv("MY_API_KEY")
       }
   }
   ```

4. **Stop vs Terminate**: Use `stop_pod()` to pause a pod and save costs, then `resume_pod()` later. Use `terminate_pod()` only when completely done.

5. **Port Forwarding for Services**: Use background execution with port forwarding for interactive services:
   ```python
   manager.execute_command(
       "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser",
       background=True,
       port_forward=(8888, 8888)
   )
   ```

6. **Transfer Before Execute**: Always transfer your code/data before running commands:
   ```python
   manager.transfer_data_to_pod("./code", "/workspace/")
   manager.execute_command("cd /workspace/code && python main.py")
   ```

7. **Download Results After Processing**: Remember to download your results before terminating the pod:
   ```python
   # Download model checkpoints, logs, and results
   manager.download_data_from_pod("/workspace/results", "./local_results")
   manager.download_data_from_pod("runs", "./tensorboard_logs")
   manager.terminate_pod()
   ```

## Troubleshooting

### SSH Connection Issues

If you encounter SSH connection errors:
- Ensure `start_ssh: True` in your pod configuration
- Wait for the pod to be fully running with `is_pod_running()`
- Check that `support_public_ip: True` is set

### Port Forwarding Not Working

- Verify the port is exposed in pod configuration: `"ports": "6006/http,22/tcp"`
- Ensure you're using `background=True` with `port_forward`
- Check that no other service is using the local port

### File Transfer Failures

- Confirm the pod is running before transferring
- Verify local file paths are correct
- Ensure sufficient disk space on the pod

## Requirements

- Python 3.11+
- `runpod>=1.7.13`
- SSH client (scp, ssh) installed on your system

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [RunPod Documentation](https://docs.runpod.io/)
- [RunPod API Reference](https://graphql-spec.runpod.io/)
