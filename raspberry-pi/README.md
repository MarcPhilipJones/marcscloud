# Raspberry Pi 5 SSH Client

A Python project for connecting to and managing your Raspberry Pi 5 over SSH.

## Overview

This project provides a Python client to connect to your Raspberry Pi 5 via SSH, enabling remote command execution, file transfers, and system monitoring.

## Setup

### Prerequisites

- Python 3.11 or higher
- Raspberry Pi 5 with SSH enabled
- Network access to the Pi (192.168.0.111)

### Installation

1. Install the package in development mode:
   ```powershell
   cd raspberry-pi
   pip install -e .
   ```

2. The `.env` file is pre-configured with your Pi credentials.

## Usage

### Command Line

```powershell
# Run an interactive shell
python -m raspberry_pi

# Execute a single command
python -m raspberry_pi --cmd "ls -la"

# Get system info
python -m raspberry_pi --info

# Check disk usage
python -m raspberry_pi --disk

# Check memory usage
python -m raspberry_pi --memory

# Check running containers (Docker/Portainer)
python -m raspberry_pi --containers
```

### As a Module

```python
from raspberry_pi import PiClient

# Create client (uses .env credentials by default)
with PiClient() as pi:
    # Run a command
    result = pi.run("ls -la")
    print(result.stdout)
    
    # Get system info
    info = pi.get_system_info()
    print(f"Hostname: {info['hostname']}")
    print(f"CPU Temp: {info['cpu_temp']}°C")
    
    # List Docker containers
    containers = pi.list_containers()
    for c in containers:
        print(f"{c['name']}: {c['status']}")
```

## Features

- **SSH Command Execution**: Run any command on the Pi
- **System Monitoring**: CPU temperature, memory, disk usage
- **Docker/Portainer Integration**: List and manage containers
- **File Transfer**: Upload and download files via SFTP
- **Interactive Shell**: Connect for interactive sessions

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `PI_HOST` | Raspberry Pi IP address | `192.168.0.111` |
| `PI_USER` | SSH username | `admin` |
| `PI_PASSWORD` | SSH password | (in .env) |
| `PI_PORT` | SSH port | `22` |

## Security Note

⚠️ The `.env` file contains your SSH credentials. It's included in `.gitignore` to prevent accidental commits.

## License

Internal use only.
