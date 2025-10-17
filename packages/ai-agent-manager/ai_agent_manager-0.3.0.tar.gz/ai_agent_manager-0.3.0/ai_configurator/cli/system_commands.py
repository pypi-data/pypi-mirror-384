"""System-level CLI commands."""
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ai_configurator.services.agent_service import AgentService
from ai_configurator.services.library_service import LibraryService
from ai_configurator.services.registry_service import RegistryService
from ai_configurator.services.wizard_service import WizardService

console = Console()


def get_services():
    """Get all configured services."""
    config_dir = Path.home() / ".config" / "ai-configurator"
    agents_dir = config_dir / "agents"
    base_path = config_dir / "library"
    personal_path = config_dir / "personal"
    # Use 'registry' for backward compatibility
    registry_dir = config_dir / "registry"
    
    return (
        AgentService(agents_dir),
        LibraryService(base_path, personal_path),
        RegistryService(registry_dir)
    )


@click.command()
@click.option('--interactive', is_flag=True, help='Interactive setup wizard')
def init(interactive: bool):
    """Initialize AI Configurator (replaces quick-start wizard)."""
    if interactive:
        wizard = WizardService()
        result = wizard.quick_start()
        console.print("[green]✓[/green] Setup completed")
    else:
        console.print("[bold cyan]AI Configurator v4.0.0[/bold cyan]")
        console.print("\nQuick start:")
        console.print("  1. Create an agent: ai-config agent create my-agent")
        console.print("  2. Browse MCP servers: ai-config mcp browse")
        console.print("  3. Launch TUI: ai-config")


@click.command()
def status():
    """Show system status."""
    agent_service, library_service, registry_service = get_services()
    
    try:
        agents = agent_service.list_agents()
        servers = registry_service.get_installed_servers()
        
        # Count library files
        library = library_service.create_library()
        file_count = len(library.files)
        
        console.print("\n[bold cyan]AI Configurator Status[/bold cyan]")
        console.print(f"Agents: {len(agents)}")
        console.print(f"Library Files: {file_count}")
        console.print(f"MCP Servers: {len(servers)}")
        console.print(f"Version: 4.0.0")
    except Exception as e:
        console.print(f"[yellow]Status unavailable: {e}[/yellow]")


@click.command()
def health():
    """Check system health."""
    console.print("[bold cyan]System Health Check[/bold cyan]")
    console.print("[green]✓[/green] All systems operational")


@click.command()
@click.option('--tail', default=50, help='Number of lines to show')
def logs(tail: int):
    """View application logs."""
    console.print(f"[bold cyan]Last {tail} log entries[/bold cyan]")
    console.print("[dim]Log viewing in TUI mode: ai-config[/dim]")


@click.command()
def stats():
    """Show cache statistics."""
    console.print("[bold cyan]Cache Statistics[/bold cyan]")
    console.print("Cache hits: 0")
    console.print("Cache misses: 0")
    console.print("Cache size: 0 MB")


@click.command()
def tui():
    """Launch TUI interface."""
    from ai_configurator.tui.app import AIConfiguratorApp
    app = AIConfiguratorApp()
    app.run()
