"""
CLI commands for library synchronization.
"""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ..models.sync_models import LibrarySync
from ..services.sync_service import SyncService
from ..core.config import ConfigManager


@click.group(name="library")
@click.pass_context
def library_group(ctx):
    """Library synchronization commands."""
    pass


@library_group.command()
@click.option("--interactive/--no-interactive", default=True, help="Interactive conflict resolution")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.pass_context
def sync(ctx, interactive: bool, dry_run: bool):
    """Synchronize personal library with base library."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up library sync
        library_sync = LibrarySync(
            base_path=config.library_config.base_library_path,
            personal_path=config.library_config.personal_library_path,
            backup_path=config.library_config.personal_library_path.parent / "backups"
        )
        
        # Create sync service
        sync_service = SyncService(console)
        
        if dry_run:
            console.print("🔍 Dry run mode - detecting conflicts...")
            conflicts = sync_service.detect_conflicts(library_sync)
            sync_service.display_conflicts(conflicts)
            
            if conflicts:
                console.print(f"\n📊 Summary: {len(conflicts)} conflicts detected")
                console.print("Run without --dry-run to resolve conflicts")
            else:
                console.print("✅ No conflicts detected. Library is up to date!")
        else:
            # Perform actual sync
            sync_history = sync_service.sync_library(library_sync, interactive)
            
            # Display results
            if sync_history.success:
                console.print(f"✅ Sync completed successfully!")
                console.print(f"📊 Conflicts detected: {sync_history.conflicts_detected}")
                console.print(f"📊 Conflicts resolved: {sync_history.conflicts_resolved}")
            else:
                console.print(f"❌ Sync failed or incomplete")
                console.print(f"📊 Conflicts detected: {sync_history.conflicts_detected}")
                console.print(f"📊 Conflicts resolved: {sync_history.conflicts_resolved}")
    
    except Exception as e:
        console.print(f"❌ Error during sync: {e}")
        raise click.ClickException(str(e))


@library_group.command()
@click.option("--file", "-f", help="Show diff for specific file")
@click.option("--summary", is_flag=True, help="Show summary of differences")
@click.pass_context
def diff(ctx, file: Optional[str], summary: bool):
    """Show differences between base and personal library."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up library sync
        library_sync = LibrarySync(
            base_path=config.library_config.base_library_path,
            personal_path=config.library_config.personal_library_path,
            backup_path=config.library_config.personal_library_path.parent / "backups"
        )
        
        # Create sync service
        sync_service = SyncService(console)
        
        # Detect conflicts (which are essentially diffs)
        conflicts = sync_service.detect_conflicts(library_sync)
        
        if file:
            # Show diff for specific file
            conflict = next((c for c in conflicts if c.file_path == file), None)
            if conflict:
                sync_service.display_diff(conflict)
            else:
                console.print(f"No differences found for file: {file}")
        elif summary:
            # Show summary table
            if conflicts:
                table = Table(title="Library Differences Summary")
                table.add_column("File", style="cyan")
                table.add_column("Status", style="yellow")
                table.add_column("Base Hash", style="dim")
                table.add_column("Personal Hash", style="dim")
                
                for conflict in conflicts:
                    table.add_row(
                        conflict.file_path,
                        "Modified",
                        conflict.base_hash[:8] + "...",
                        conflict.personal_hash[:8] + "..."
                    )
                
                console.print(table)
            else:
                console.print("✅ No differences found between base and personal library")
        else:
            # Show all diffs
            if conflicts:
                for conflict in conflicts:
                    sync_service.display_diff(conflict)
                    console.print()  # Add spacing
            else:
                console.print("✅ No differences found between base and personal library")
    
    except Exception as e:
        console.print(f"❌ Error showing diff: {e}")
        raise click.ClickException(str(e))


@library_group.command()
@click.option("--force", is_flag=True, help="Force update without confirmation")
@click.pass_context
def update(ctx, force: bool):
    """Update personal library from base library (alias for sync)."""
    console = Console()
    
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask("This will update your personal library. Continue?"):
            console.print("Update cancelled.")
            return
    
    # Call sync command
    ctx.invoke(sync, interactive=True, dry_run=False)


@library_group.command()
@click.pass_context
def status(ctx):
    """Show library synchronization status."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up library sync
        library_sync = LibrarySync(
            base_path=config.library_config.base_library_path,
            personal_path=config.library_config.personal_library_path,
            backup_path=config.library_config.personal_library_path.parent / "backups"
        )
        
        # Create sync service
        sync_service = SyncService(console)
        
        # Check status
        conflicts = sync_service.detect_conflicts(library_sync)
        
        # Display status
        table = Table(title="Library Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Base Library", str(library_sync.base_path))
        table.add_row("Personal Library", str(library_sync.personal_path))
        table.add_row("Backup Directory", str(library_sync.backup_path))
        table.add_row("Conflicts", str(len(conflicts)))
        
        if conflicts:
            table.add_row("Status", "⚠️  Conflicts detected", style="yellow")
        else:
            table.add_row("Status", "✅ Synchronized", style="green")
        
        console.print(table)
        
        if conflicts:
            console.print(f"\n⚠️  {len(conflicts)} conflicts detected. Run 'ai-config library sync' to resolve.")
    
    except Exception as e:
        console.print(f"❌ Error checking status: {e}")
        raise click.ClickException(str(e))


# Add the library group to the main CLI
def register_commands(cli_group):
    """Register library commands with the main CLI."""
    cli_group.add_command(library_group)
