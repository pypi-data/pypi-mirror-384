"""
Enhanced synchronization CLI commands.
"""

import click
from rich.console import Console

from ..services.enhanced_sync_service import EnhancedSyncService


@click.group(name="sync")
def sync_group():
    """Enhanced library synchronization commands."""
    pass


@sync_group.command()
@click.option("--interactive/--no-interactive", default=True, help="Interactive conflict resolution")
def all(interactive: bool):
    """Sync all configured libraries (local and remote)."""
    console = Console()
    sync_service = EnhancedSyncService(console)
    
    console.print("🔄 Starting comprehensive library sync...")
    
    results = sync_service.sync_all_libraries(interactive)
    sync_service.display_sync_summary(results)


@sync_group.command()
@click.argument("source_type", type=click.Choice(["local", "remote"]))
@click.option("--interactive/--no-interactive", default=True, help="Interactive conflict resolution")
def source(source_type: str, interactive: bool):
    """Sync a specific library source."""
    console = Console()
    sync_service = EnhancedSyncService(console)
    
    console.print(f"🔄 Syncing {source_type} library...")
    
    result = sync_service.sync_specific_source(source_type, interactive)
    
    if result:
        if result.success:
            console.print(f"✅ {source_type.title()} library sync completed successfully")
        else:
            console.print(f"❌ {source_type.title()} library sync failed")
    else:
        console.print(f"⚠️  {source_type.title()} library sync not available")


@sync_group.command()
def status():
    """Show status of all library sources."""
    console = Console()
    sync_service = EnhancedSyncService(console)
    
    sync_service.list_library_sources()


@sync_group.command()
@click.argument("repo_url")
@click.option("--path", "-p", help="Local path for the library")
def configure(repo_url: str, path: str):
    """Configure remote library repository."""
    console = Console()
    sync_service = EnhancedSyncService(console)
    
    success = sync_service.configure_remote_library(repo_url, path)
    
    if success:
        console.print("✅ Remote library configured successfully")
        console.print("Use 'sync all' or 'sync source remote' to sync with the remote repository")
    else:
        console.print("❌ Failed to configure remote library")


@sync_group.command()
def info():
    """Show detailed information about library sources."""
    console = Console()
    sync_service = EnhancedSyncService(console)
    
    status = sync_service.get_library_status()
    
    # Display local library info
    local = status["local"]
    console.print("📁 [bold]Local Libraries[/bold]")
    console.print(f"   Base: {local['base_path']} ({local['base_files']} files)")
    console.print(f"   Personal: {local['personal_path']} ({local['personal_files']} files)")
    
    # Display remote library info
    remote = status["remote"]
    console.print("\n🌐 [bold]Remote Library[/bold]")
    
    if remote.get("configured", True):
        console.print(f"   URL: {remote['url']}")
        console.print(f"   Local: {remote['local_path']} ({remote['files']} files)")
        
        if remote["exists"]:
            if remote["is_git_repo"]:
                git_status = remote["git_status"]
                if "error" not in git_status:
                    console.print(f"   Branch: {git_status['current_branch']}")
                    console.print(f"   Latest: {git_status['latest_commit']['hash']} - {git_status['latest_commit']['message']}")
                    
                    if git_status["has_changes"]:
                        console.print("   Status: 🔄 Has uncommitted changes")
                    else:
                        console.print("   Status: ✅ Clean working directory")
                else:
                    console.print(f"   Status: ❌ Git error - {git_status['error']}")
            else:
                console.print("   Status: ⚠️  Directory exists but not a Git repository")
        else:
            console.print("   Status: ❌ Not cloned locally")
    else:
        console.print("   Status: ➖ Not configured")


def register_enhanced_sync_commands(cli):
    """Register enhanced sync commands with the main CLI."""
    cli.add_command(sync_group)
