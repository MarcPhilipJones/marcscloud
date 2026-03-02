"""Azure CLI command runner."""

import subprocess
import shutil
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of an Azure CLI command execution."""
    
    success: bool
    output: str
    error: str
    return_code: int


class AzureRunner:
    """Executes Azure CLI commands."""
    
    def __init__(self) -> None:
        """Initialize the Azure CLI runner."""
        self._az_path: str | None = None
    
    def is_installed(self) -> bool:
        """Check if Azure CLI is installed."""
        return shutil.which("az") is not None
    
    def execute(self, command: str, output_json: bool = False) -> CommandResult:
        """Execute an Azure CLI command.
        
        Args:
            command: The Azure CLI command (without 'az' prefix)
            output_json: If True, add --output json flag
            
        Returns:
            CommandResult with success status and output/error
        """
        full_command = f"az {command}"
        
        if output_json and "--output" not in command:
            full_command += " --output json"
        
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            
            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip(),
                return_code=result.returncode,
            )
            
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output="",
                error="Command timed out after 5 minutes",
                return_code=-1,
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                return_code=-1,
            )
    
    def execute_interactive(self, command: str) -> int:
        """Execute an Azure CLI command interactively (for login, etc.).
        
        Args:
            command: The Azure CLI command (without 'az' prefix)
            
        Returns:
            The return code of the command
        """
        full_command = f"az {command}"
        
        try:
            result = subprocess.run(full_command, shell=True)
            return result.returncode
        except Exception:
            return -1
