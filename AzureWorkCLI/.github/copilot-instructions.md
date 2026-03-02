# AzureWorkCLI - Copilot Instructions

This is a Python CLI tool for running Azure CLI commands with enhanced output formatting.

## Project Structure

- `src/azureworkcli/` - Main source code
  - `cli.py` - CLI entry point using Click
  - `azure_runner.py` - Azure CLI execution logic
- `tests/` - Test files
- `pyproject.toml` - Project configuration

## Development

- Python 3.10+ with virtual environment in `.venv`
- Uses Click for CLI framework and Rich for output formatting
- Run CLI with: `python -m azureworkcli.cli`

## Commands

- `azwork check` - Verify Azure CLI installation and authentication
- `azwork run <command>` - Execute any Azure CLI command
- `azwork resources` - List Azure resources

## Debugging

Use the launch configurations in `.vscode/launch.json`:
- **AzureWorkCLI: Check** - Run the check command
- **AzureWorkCLI: Run Command** - Run `az group list`
- **AzureWorkCLI: Custom Args** - Prompt for custom arguments
