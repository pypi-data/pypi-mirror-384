"""Library management CLI commands."""
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ai_configurator.services.library_service import LibraryService
from ai_configurator.services.sync_service import SyncService
from ai_configurator.services.file_service import FileService

console = Console()


def get_library_service():
    """Get configured library service."""
    config_dir = Path.home() / ".config" / "ai-configurator"
    base_path = config_dir / "library"
    personal_path = config_dir / "personal"
    return LibraryService(base_path, personal_path)


@click.group()
def library():
    """Library management commands."""
    pass


@library.command()
def status():
    """Show library status."""
    service = get_library_service()
    
    try:
        library = service.create_library()
        
        # Count base vs personal files
        base_count = sum(1 for f in library.files.values() if f.source.value == 'base')
        personal_count = sum(1 for f in library.files.values() if f.source.value == 'personal')
        
        console.print(f"\n[bold cyan]Library Status[/bold cyan]")
        console.print(f"Base Files: {base_count}")
        console.print(f"Personal Files: {personal_count}")
        console.print(f"Total Files: {len(library.files)}")
    except Exception as e:
        console.print(f"[yellow]Status unavailable: {e}[/yellow]")


@library.command()
@click.option('--interactive', is_flag=True, help='Interactive conflict resolution')
def sync(interactive: bool):
    """Sync library with conflict resolution."""
    from ai_configurator.models.sync_models import LibrarySync
    from pathlib import Path
    
    service = get_library_service()
    sync_service = SyncService()
    
    try:
        library = service.create_library()
        config_dir = Path.home() / ".config" / "ai-configurator"
        backup_path = config_dir / "backups"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        library_sync = LibrarySync(
            base_path=library.base_path,
            personal_path=library.personal_path,
            backup_path=backup_path
        )
        
        with console.status("[bold green]Syncing library..."):
            result = sync_service.sync_library(library_sync, interactive=interactive)
        
        if result.conflicts_detected > 0:
            console.print(f"[yellow]Found {result.conflicts_detected} conflicts[/yellow]")
            console.print(f"Resolved: {result.conflicts_resolved}")
            if interactive:
                console.print("[dim]Use TUI mode for interactive resolution: ai-config[/dim]")
        else:
            console.print("[green]✓[/green] Sync completed successfully")
    except Exception as e:
        console.print(f"[red]Sync error: {e}[/red]")


@library.command()
def diff():
    """Show differences between base and personal library."""
    from ai_configurator.models.sync_models import LibrarySync
    from pathlib import Path
    
    service = get_library_service()
    sync_service = SyncService()
    
    try:
        library = service.create_library()
        config_dir = Path.home() / ".config" / "ai-configurator"
        backup_path = config_dir / "backups"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        library_sync = LibrarySync(
            base_path=library.base_path,
            personal_path=library.personal_path,
            backup_path=backup_path
        )
        
        diffs = sync_service.get_diff(library_sync)
        
        if not diffs:
            console.print("[green]No differences found.[/green]")
            return
        
        table = Table(title="Library Differences")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="yellow")
        
        for diff in diffs:
            table.add_row(diff.file_path, diff.status.value)
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@library.command()
def update():
    """Update from base library."""
    service = get_library_service()
    
    with console.status("[bold green]Updating library..."):
        service.update_from_base()
    
    console.print("[green]✓[/green] Library updated")


@library.command()
@click.argument('pattern')
@click.option('--agent', help='Agent name to add files to')
def files(pattern: str, agent: str):
    """Discover files matching pattern."""
    service = FileService()
    result = service.discover_files(pattern)
    
    console.print(f"\n[bold cyan]Found {len(result.files)} files[/bold cyan]")
    
    for file in result.files[:10]:  # Show first 10
        console.print(f"  {file.path}")
    
    if len(result.files) > 10:
        console.print(f"  ... and {len(result.files) - 10} more")
    
    if agent:
        console.print(f"\n[dim]Adding to agent: {agent}[/dim]")


@library.command()
@click.argument('pattern')
@click.argument('agent')
def add(pattern: str, agent: str):
    """Add files to agent."""
    service = FileService()
    result = service.add_files_to_agent(agent, pattern)
    console.print(f"[green]✓[/green] Added {result.count} files to {agent}")


@library.command()
@click.argument('agent')
@click.option('--enable/--disable', default=True, help='Enable or disable watching')
def watch(agent: str, enable: bool):
    """Enable/disable file watching for agent."""
    service = FileService()
    
    if enable:
        service.enable_watching(agent)
        console.print(f"[green]✓[/green] Enabled file watching for {agent}")
    else:
        service.disable_watching(agent)
        console.print(f"[yellow]Disabled file watching for {agent}[/yellow]")
