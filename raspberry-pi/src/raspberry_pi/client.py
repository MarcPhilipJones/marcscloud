"""SSH client for Raspberry Pi 5."""

import os
from dataclasses import dataclass
from typing import Any, Optional

import paramiko
from dotenv import load_dotenv


@dataclass
class CommandResult:
    """Result of a command execution."""
    
    command: str
    stdout: str
    stderr: str
    exit_code: int
    
    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.exit_code == 0
    
    @property
    def output(self) -> str:
        """Get combined output (stdout + stderr)."""
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        return "\n".join(parts)


class PiClient:
    """SSH client for connecting to Raspberry Pi 5."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize the Pi SSH client.
        
        Args:
            host: Pi IP address (or set PI_HOST env var)
            port: SSH port (or set PI_PORT env var, default 22)
            user: SSH username (or set PI_USER env var)
            password: SSH password (or set PI_PASSWORD env var)
        """
        load_dotenv()
        
        self.host = host or os.getenv("PI_HOST", "192.168.0.111")
        self.port = port or int(os.getenv("PI_PORT", "22"))
        self.user = user or os.getenv("PI_USER", "admin")
        self.password = password or os.getenv("PI_PASSWORD", "")
        
        if not self.password:
            raise ValueError(
                "Missing SSH password. Set PI_PASSWORD environment variable "
                "or pass password parameter."
            )
        
        self._client: Optional[paramiko.SSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None
    
    def connect(self) -> None:
        """Establish SSH connection to the Pi."""
        if self._client is not None:
            return
        
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        self._client.connect(
            hostname=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            timeout=10,
        )
    
    def disconnect(self) -> None:
        """Close the SSH connection."""
        if self._sftp:
            self._sftp.close()
            self._sftp = None
        
        if self._client:
            self._client.close()
            self._client = None
    
    def run(self, command: str, timeout: float = 30) -> CommandResult:
        """
        Execute a command on the Pi.
        
        Args:
            command: The command to execute
            timeout: Command timeout in seconds
        
        Returns:
            CommandResult with stdout, stderr, and exit code
        """
        self.connect()
        
        stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
        
        exit_code = stdout.channel.recv_exit_status()
        stdout_text = stdout.read().decode("utf-8").strip()
        stderr_text = stderr.read().decode("utf-8").strip()
        
        return CommandResult(
            command=command,
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=exit_code,
        )
    
    @property
    def sftp(self) -> paramiko.SFTPClient:
        """Get SFTP client for file transfers."""
        self.connect()
        
        if self._sftp is None:
            self._sftp = self._client.open_sftp()
        
        return self._sftp
    
    # =========================================================================
    # System Information
    # =========================================================================
    
    def get_system_info(self) -> dict[str, Any]:
        """Get system information about the Pi."""
        info = {}
        
        # Hostname
        result = self.run("hostname")
        info["hostname"] = result.stdout
        
        # OS info
        result = self.run("cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"'")
        info["os"] = result.stdout
        
        # Kernel
        result = self.run("uname -r")
        info["kernel"] = result.stdout
        
        # CPU temperature
        result = self.run("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0")
        try:
            info["cpu_temp"] = round(int(result.stdout) / 1000, 1)
        except ValueError:
            info["cpu_temp"] = None
        
        # Uptime
        result = self.run("uptime -p")
        info["uptime"] = result.stdout.replace("up ", "")
        
        # CPU model
        result = self.run("cat /proc/cpuinfo | grep 'Model' | head -1 | cut -d':' -f2")
        info["model"] = result.stdout.strip()
        
        return info
    
    def get_memory_info(self) -> dict[str, Any]:
        """Get memory usage information."""
        result = self.run("free -m | grep Mem")
        parts = result.stdout.split()
        
        if len(parts) >= 3:
            total = int(parts[1])
            used = int(parts[2])
            return {
                "total_mb": total,
                "used_mb": used,
                "free_mb": total - used,
                "percent_used": round((used / total) * 100, 1) if total > 0 else 0,
            }
        
        return {"total_mb": 0, "used_mb": 0, "free_mb": 0, "percent_used": 0}
    
    def get_disk_info(self) -> list[dict[str, Any]]:
        """Get disk usage information."""
        result = self.run("df -h | grep -E '^/dev/'")
        disks = []
        
        for line in result.stdout.split("\n"):
            parts = line.split()
            if len(parts) >= 6:
                disks.append({
                    "device": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "percent_used": parts[4],
                    "mount": parts[5],
                })
        
        return disks
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        result = self.run("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
        try:
            return float(result.stdout.replace(",", "."))
        except ValueError:
            return 0.0
    
    # =========================================================================
    # Docker / Portainer
    # =========================================================================
    
    def list_containers(self) -> list[dict[str, str]]:
        """List Docker containers."""
        result = self.run("docker ps -a --format '{{.Names}}|{{.Status}}|{{.Image}}' 2>/dev/null")
        
        if not result.success or not result.stdout:
            return []
        
        containers = []
        for line in result.stdout.split("\n"):
            parts = line.split("|")
            if len(parts) >= 3:
                containers.append({
                    "name": parts[0],
                    "status": parts[1],
                    "image": parts[2],
                })
        
        return containers
    
    def start_container(self, name: str) -> CommandResult:
        """Start a Docker container."""
        return self.run(f"docker start {name}")
    
    def stop_container(self, name: str) -> CommandResult:
        """Stop a Docker container."""
        return self.run(f"docker stop {name}")
    
    def restart_container(self, name: str) -> CommandResult:
        """Restart a Docker container."""
        return self.run(f"docker restart {name}")
    
    def container_logs(self, name: str, lines: int = 50) -> str:
        """Get container logs."""
        result = self.run(f"docker logs --tail {lines} {name} 2>&1")
        return result.output
    
    # =========================================================================
    # File Operations
    # =========================================================================
    
    def upload_file(self, local_path: str, remote_path: str) -> None:
        """Upload a file to the Pi."""
        self.sftp.put(local_path, remote_path)
    
    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download a file from the Pi."""
        self.sftp.get(remote_path, local_path)
    
    def list_directory(self, path: str = ".") -> list[str]:
        """List files in a directory."""
        return self.sftp.listdir(path)
    
    def read_file(self, path: str) -> str:
        """Read a file from the Pi."""
        with self.sftp.open(path, "r") as f:
            return f.read().decode("utf-8")
    
    # =========================================================================
    # Context Manager
    # =========================================================================
    
    def __enter__(self) -> "PiClient":
        self.connect()
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.disconnect()
