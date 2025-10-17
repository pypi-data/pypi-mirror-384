"""MCP server management CLI commands."""
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ai_configurator.services.registry_service import RegistryService

console = Console()


def get_registry_service():
    """Get configured registry service."""
    # Use 'registry' for backward compatibility
    registry_dir = Path.home() / ".config" / "ai-configurator" / "registry"
    return RegistryService(registry_dir)


@click.group()
def mcp():
    """MCP server management commands."""
    pass


@mcp.command()
def list():
    """List installed MCP servers."""
    service = get_registry_service()
    servers = service.get_installed_servers()
    
    if not servers:
        console.print("[yellow]No MCP servers installed.[/yellow]")
        return
    
    table = Table(title="Installed MCP Servers")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Status", style="magenta")
    table.add_column("Install Date", style="blue")
    
    for server in servers:
        table.add_row(
            server.server_name,
            server.installed_version or "Unknown",
            server.health_status.value,
            server.install_date.strftime("%Y-%m-%d") if server.install_date else "Unknown"
        )
    
    console.print(table)


@mcp.command()
@click.option('--category', help='Filter by category')
def browse(category: str):
    """Browse available MCP servers."""
    service = get_registry_service()
    servers = service.search_servers(category=category)
    
    if not servers:
        console.print("[yellow]No servers found.[/yellow]")
        return
    
    table = Table(title="Available MCP Servers")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Description", style="white")
    table.add_column("Rating", style="yellow")
    
    for server in servers:
        table.add_row(
            server.name,
            server.category,
            server.description[:50] + "..." if len(server.description) > 50 else server.description,
            f"⭐ {server.rating}"
        )
    
    console.print(table)


@mcp.command()
@click.argument('query')
def search(query: str):
    """Search for MCP servers."""
    service = get_registry_service()
    servers = service.search_servers(query)
    
    if not servers:
        console.print(f"[yellow]No servers found matching '{query}'.[/yellow]")
        return
    
    console.print(f"\n[bold cyan]Found {len(servers)} servers[/bold cyan]")
    for server in servers:
        console.print(f"  {server.name} - {server.description}")


@mcp.command()
@click.argument('name')
@click.option('--interactive', is_flag=True, help='Interactive configuration')
def install(name: str, interactive: bool):
    """Install MCP server."""
    service = get_registry_service()
    
    with console.status(f"[bold green]Installing {name}..."):
        result = service.install_server(name)
    
    if result.success:
        console.print(f"[green]✓[/green] Installed {name}")
    else:
        console.print(f"[red]Failed to install {name}[/red]")


@mcp.command()
@click.argument('name')
def configure(name: str):
    """Configure MCP server."""
    console.print(f"[yellow]Configuring server: {name}[/yellow]")
    console.print("[dim]Use TUI mode for interactive configuration: ai-config[/dim]")


@mcp.command()
def init_registry():
    """Initialize MCP server registry."""
    service = get_registry_service()
    service.create_sample_registry()
    console.print("[green]✓[/green] Initialized MCP registry")
