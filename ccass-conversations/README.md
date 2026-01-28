# CCaSS Conversations

A Python project for retrieving and processing conversations from Microsoft Dataverse.

## Overview

This project connects to Microsoft Dataverse to retrieve conversation records, enabling analysis and processing of customer service conversations.

## Setup

### Prerequisites

- Python 3.11 or higher
- Azure AD application registration with Dataverse permissions

### Installation

1. Create a virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install the package in development mode:
   ```powershell
   pip install -e .
   ```

3. Copy the example environment file and configure your credentials:
   ```powershell
   copy .env.example .env
   ```

4. Edit `.env` with your Dataverse credentials:
   - `DATAVERSE_URL`: Your Dataverse environment URL
   - `AZURE_CLIENT_ID`: Azure AD application client ID
   - `AZURE_TENANT_ID`: Azure AD tenant ID
   - `AZURE_CLIENT_SECRET`: Azure AD application client secret

## Usage

### Retrieve Conversations

```powershell
python -m ccass_conversations
```

### As a Module

```python
from ccass_conversations import DataverseClient

client = DataverseClient()
conversations = client.get_conversations()
```

## Project Structure

```
ccass-conversations/
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── .env.example            # Example environment configuration
└── src/
    └── ccass_conversations/
        ├── __init__.py     # Package initialization
        ├── __main__.py     # CLI entry point
        ├── client.py       # Dataverse API client
        └── models.py       # Data models
```

## Configuration

The following environment variables are required:

| Variable | Description |
|----------|-------------|
| `DATAVERSE_URL` | Base URL for your Dataverse environment (e.g., `https://org.crm.dynamics.com`) |
| `AZURE_CLIENT_ID` | Azure AD application (client) ID |
| `AZURE_TENANT_ID` | Azure AD directory (tenant) ID |
| `AZURE_CLIENT_SECRET` | Azure AD application client secret |

## License

Internal use only.
