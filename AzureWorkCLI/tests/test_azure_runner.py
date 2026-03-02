"""Tests for the Azure CLI runner."""

import pytest
from azureworkcli.azure_runner import AzureRunner, CommandResult


class TestAzureRunner:
    """Tests for AzureRunner class."""
    
    def test_is_installed(self) -> None:
        """Test checking if Azure CLI is installed."""
        runner = AzureRunner()
        # This will return True or False depending on the system
        result = runner.is_installed()
        assert isinstance(result, bool)
    
    def test_command_result_dataclass(self) -> None:
        """Test CommandResult dataclass."""
        result = CommandResult(
            success=True,
            output="test output",
            error="",
            return_code=0,
        )
        assert result.success is True
        assert result.output == "test output"
        assert result.error == ""
        assert result.return_code == 0
