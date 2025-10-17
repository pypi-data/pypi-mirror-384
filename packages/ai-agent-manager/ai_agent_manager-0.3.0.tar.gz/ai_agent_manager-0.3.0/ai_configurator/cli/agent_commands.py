"""Agent management CLI commands."""
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ai_configurator.services.agent_service import AgentService
from ai_configurator.services.wizard_service import WizardService

console = Console()


def get_agent_service():
    """Get configured agent service."""
    agents_dir = Path.home() / ".config" / "ai-configurator" / "agents"
    return AgentService(agents_dir)


@click.group()
def agent():
    """Agent management commands."""
    pass


@agent.command()
def list():
    """List all agents."""
    service = get_agent_service()
    agents = service.list_agents()
    
    if not agents:
        console.print("[yellow]No agents found.[/yellow]")
        return
    
    table = Table(title="Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Tool", style="green")
    table.add_column("Resources", style="blue")
    table.add_column("Status", style="magenta")
    
    for agent in agents:
        table.add_row(
            agent.name,
            agent.tool_type.value,
            str(len(agent.config.resources)),
            agent.health_status.value
        )
    
    console.print(table)


@agent.command()
@click.argument('name')
def show(name: str):
    """Show agent details."""
    service = get_agent_service()
    agent = service.get_agent(name)
    
    if not agent:
        console.print(f"[red]Agent '{name}' not found.[/red]")
        raise click.Abort()
    
    console.print(f"\n[bold cyan]Agent: {agent.name}[/bold cyan]")
    console.print(f"Tool: {agent.tool_type.value}")
    console.print(f"Resources: {len(agent.config.resources)}")
    console.print(f"Status: {agent.health_status.value}")


@agent.command()
@click.argument('name')
@click.option('--tool', type=click.Choice(['q-cli', 'cursor', 'windsurf']), help='Tool type')
@click.option('--interactive', is_flag=True, help='Interactive creation wizard')
def create(name: str, tool: str, interactive: bool):
    """Create new agent."""
    if interactive:
        wizard = WizardService()
        result = wizard.create_agent_wizard(name)
        console.print(f"[green]✓[/green] Created agent: {result.agent_name}")
    else:
        service = get_agent_service()
        agent = service.create_agent(name, tool or 'q-cli')
        console.print(f"[green]✓[/green] Created agent: {agent.name}")


@agent.command()
@click.argument('name')
def edit(name: str):
    """Edit agent configuration."""
    console.print(f"[yellow]Opening editor for agent: {name}[/yellow]")
    console.print("[dim]Use TUI mode for interactive editing: ai-config[/dim]")


@agent.command()
@click.argument('name')
@click.option('--force', is_flag=True, help='Force deletion without confirmation')
def delete(name: str, force: bool):
    """Delete agent."""
    if not force:
        if not click.confirm(f"Delete agent '{name}'?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return
    
    service = get_agent_service()
    service.delete_agent(name)
    console.print(f"[green]✓[/green] Deleted agent: {name}")


@agent.command()
@click.argument('name')
def export(name: str):
    """Export agent to target tool."""
    service = get_agent_service()
    result = service.export_agent(name)
    console.print(f"[green]✓[/green] Exported agent: {name}")
    console.print(f"Location: {result}")
