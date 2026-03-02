"""Raspberry Pi 5 SSH Client - Connect and manage your Pi remotely."""

from .client import PiClient, CommandResult

__all__ = ["PiClient", "CommandResult"]
__version__ = "0.1.0"
