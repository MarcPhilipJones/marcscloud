"""Main CLI entry point for AzureWorkCLI."""

import click
from rich.console import Console

from .azure_runner import AzureRunner

console = Console()


@click.group()
@click.version_option(package_name="azureworkcli")
@click.pass_context
def main(ctx: click.Context) -> None:
    """AzureWorkCLI - A CLI tool for running Azure CLI commands."""
    ctx.ensure_object(dict)
    ctx.obj["runner"] = AzureRunner()


@main.command()
@click.argument("command", nargs=-1, required=True)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def run(ctx: click.Context, command: tuple[str, ...], output_json: bool) -> None:
    """Run an Azure CLI command.
    
    Example: azwork run group list
    """
    runner: AzureRunner = ctx.obj["runner"]
    cmd_str = " ".join(command)
    
    result = runner.execute(cmd_str, output_json=output_json)
    
    if result.success:
        if result.output:
            console.print(result.output)
    else:
        console.print(f"[red]Error:[/red] {result.error}", style="bold red")
        raise SystemExit(1)


@main.command()
@click.pass_context
def check(ctx: click.Context) -> None:
    """Check if Azure CLI is installed and authenticated."""
    runner: AzureRunner = ctx.obj["runner"]
    
    # Check Azure CLI installation
    console.print("[bold]Checking Azure CLI...[/bold]")
    
    if not runner.is_installed():
        console.print("[red]✗[/red] Azure CLI is not installed")
        console.print("  Install from: https://docs.microsoft.com/cli/azure/install-azure-cli")
        raise SystemExit(1)
    
    console.print("[green]✓[/green] Azure CLI is installed")
    
    # Check authentication
    result = runner.execute("account show", output_json=True)
    if result.success:
        console.print("[green]✓[/green] Authenticated to Azure")
        console.print(f"  Subscription: {result.output}")
    else:
        console.print("[yellow]![/yellow] Not authenticated - run 'az login' to authenticate")


@main.command()
@click.option("--resource-group", "-g", help="Filter by resource group")
@click.pass_context
def resources(ctx: click.Context, resource_group: str | None) -> None:
    """List Azure resources."""
    runner: AzureRunner = ctx.obj["runner"]
    
    cmd = "resource list"
    if resource_group:
        cmd += f" --resource-group {resource_group}"
    
    result = runner.execute(cmd, output_json=True)
    
    if result.success:
        console.print(result.output)
    else:
        console.print(f"[red]Error:[/red] {result.error}", style="bold red")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
