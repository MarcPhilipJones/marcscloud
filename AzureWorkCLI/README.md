# AzureWorkCLI

A Python CLI tool for running Azure CLI commands with enhanced output formatting.

## Prerequisites

- Python 3.10+
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) installed and configured

## Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/macOS
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Usage

### Check Azure CLI Status
```bash
azwork check
```

### Run Azure CLI Commands
```bash
# Run any Azure CLI command
azwork run group list

# Get JSON output
azwork run --json vm list

# List resources in a specific resource group
azwork resources -g my-resource-group
```

## Development

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

## Project Structure

```
AzureWorkCLI/
├── src/
│   └── azureworkcli/
│       ├── __init__.py
│       ├── cli.py           # CLI entry point
│       └── azure_runner.py  # Azure CLI execution logic
├── tests/
│   └── test_azure_runner.py
├── pyproject.toml
└── README.md
```

## License

MIT
