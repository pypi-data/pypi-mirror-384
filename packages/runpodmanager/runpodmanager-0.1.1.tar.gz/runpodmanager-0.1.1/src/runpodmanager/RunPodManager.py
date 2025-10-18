from typing import Optional
import os
import runpod
import subprocess
import logging
import sys

logger = logging.getLogger(__name__)


class RunPodManager:
    def __init__(self, api_key: Optional[str] = None) -> None:
        """RunPodManager class
        Used to manage a RunPod pod.

        Args:
            api_key (Optional[str], optional): RunPod api key. Defaults to None.

        Raises:
            ValueError: if api_key is not passed or RUNPOD_API_KEY is not found in environment variables
        """

        api_key = api_key or os.getenv("RUNPOD_API_KEY")

        if api_key is None:
            raise ValueError(
                "`RUNPOD_API_KEY` not found. Either pass it to the `api_key` parameter or set the `RUNPOD_API_KEY` environment variable"
            )

        runpod.api_key = api_key
        self.pod_id: Optional[str] = None

    def create_pod(self, pod_config: dict) -> None:
        """Creates RunPod pod

        Args:
            pod_config (dict): pod configuration
        """

        pod = runpod.create_pod(**pod_config)
        self.pod_id = pod["id"]
        logger.info(f"Initialized RunPod pod with id: {self.pod_id}")

    def connect_to_pod(self, pod_id: str) -> None:
        """Connects to existing pod

        Args:
            pod_id (str): RunPod pod id

        Raises:
            ValueError: if pod does not exist
        """

        if not runpod.get_pod(pod_id):
            raise ValueError(f"Pod: {pod_id} does not exist")

        self.pod_id = pod_id
        logger.info(f"Connected to RunPod pod with id: {self.pod_id}")

    def stop_pod(self) -> None:
        """Stops RunPod pod"""

        runpod.stop_pod(self.pod_id)
        logger.info(f"Stopped RunPod pod with id: {self.pod_id}")

    def resume_pod(self) -> None:
        """Resumes stopped RunPod pod"""

        gpu_count = runpod.get_pod(self.pod_id).get("gpuCount", 1)
        runpod.resume_pod(pod_id=self.pod_id, gpu_count=gpu_count)
        logger.info(f"Resumed RunPod pod with id: {self.pod_id}")

    def terminate_pod(self) -> None:
        """Terminates RunPod pod"""

        runpod.terminate_pod(self.pod_id)
        logger.info(f"Terminated RunPod pod with id: {self.pod_id}")

    def pod_exists(self) -> bool:
        """Checks if RunPod pod exists

        Returns:
            bool: True if pod exists, False otherwise
        """

        if self.pod_id is None:
            return False

        return bool(runpod.get_pod(self.pod_id))

    def is_pod_running(self) -> bool:
        """Checks if RunPod pod is running

        Returns:
            bool: True if pod is running, False otherwise
        """

        return self.pod_exists() and bool(runpod.get_pod(self.pod_id).get("runtime"))

    def _get_ssh_connection_info(self) -> Optional[dict]:
        """Gets SSH info for pod"""

        if not self.is_pod_running():
            raise ValueError("Cannot perform SSH operation on a non-running pod")

        try:
            pod_info = runpod.get_pod(self.pod_id)
            runtime = pod_info.get("runtime", {})

            if "ports" not in runtime:
                raise ValueError(f"Cannot retrieve SSH info for pod: {self.pod_id}")

            ssh_info = list(filter(lambda x: x["privatePort"] == 22, runtime["ports"]))
            if not ssh_info:
                raise ValueError(f"Cannot retrieve SSH info for pod: {self.pod_id}")

            ssh_info = ssh_info[0]
            ssh_port = ssh_info.get("publicPort")
            public_ip = ssh_info.get("ip")

            if public_ip and ssh_port:
                return {
                    "ip": public_ip,
                    "port": ssh_port,
                    "ssh_command": f"ssh root@{public_ip} -p {ssh_port}",
                }

        except Exception as e:
            raise Exception("Error getting SSH info") from e

    def transfer_data_to_pod(self, local_path: str, remote_path: str = "") -> None:
        """Transfers local data to runPod pod via SSH

        Args:
            local_path (str): local path
            remote_path (str, optional): remote path. Defaults to "".

        Raises:
            Exception: _description_
        """

        ssh_info = self._get_ssh_connection_info()

        try:
            scp_command = [
                "scp",
                "-P",
                str(ssh_info["port"]),
                "-o",
                "StrictHostKeyChecking=no",
                "-r",
                local_path,
                f"root@{ssh_info['ip']}:{remote_path}",
            ]

            logger.info(f"Transferring {local_path} to pod...")
            result = subprocess.run(scp_command, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("File transfer successful!")
            else:
                logger.error(f"Transfer failed: {result.stderr}")

        except Exception as e:
            raise Exception("Error during transfer") from e

    def download_data_from_pod(self, remote_path: str, local_path: str = ".") -> None:
        """Downloads data from RunPod pod to local machine via SSH

        Args:
            remote_path (str): remote path on the pod
            local_path (str, optional): local destination path. Defaults to current directory.

        Raises:
            Exception: if download fails
        """

        ssh_info = self._get_ssh_connection_info()

        try:
            scp_command = [
                "scp",
                "-P",
                str(ssh_info["port"]),
                "-o",
                "StrictHostKeyChecking=no",
                "-r",
                f"root@{ssh_info['ip']}:{remote_path}",
                local_path,
            ]

            logger.info(f"Downloading {remote_path} from pod...")
            result = subprocess.run(scp_command, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("File download successful!")
            else:
                logger.error(f"Download failed: {result.stderr}")

        except Exception as e:
            raise Exception("Error during download") from e

    def execute_command(
        self,
        command: str,
        background: bool = False,
        port_forward: tuple[int, int] = None,
    ):
        """Execute command on the pod via SSH

        Args:
            command: Command to execute
            background: If True, run command in background
            port_forward: Tuple of (local_port, remote_port) for SSH port forwarding

        Returns:
            Process object if background with port_forward, otherwise return code
        """

        ssh_info = self._get_ssh_connection_info()
        ssh_cmd = ["ssh", "-tt", f"root@{ssh_info['ip']}", "-p", str(ssh_info["port"])]

        # Add StrictHostKeyChecking=no to avoid prompt
        ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])

        if port_forward:
            local_port, remote_port = port_forward
            ssh_cmd.extend(["-L", f"{local_port}:localhost:{remote_port}"])

        if background and port_forward:
            ssh_cmd.append(command)

            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
            )

            logger.info(
                f"Started background process with port forwarding on port {local_port}"
            )
            return process

        elif background:
            # Background without port forwarding
            command = f"nohup {command} > /dev/null 2>&1 &"
            ssh_cmd.append(command)
        else:
            # Foreground execution
            ssh_cmd.append(command)

        process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        # Stream output for non-background or background without port forwarding
        for line in iter(process.stdout.readline, ""):
            print(line, end="")
            sys.stdout.flush()

        process.wait()
        return process.returncode
