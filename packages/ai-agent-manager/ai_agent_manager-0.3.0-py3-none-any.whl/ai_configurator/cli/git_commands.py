"""
Git-based library management CLI commands.
"""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm

from ..services.git_library_service import GitLibraryService
from ..core.config import ConfigProxy


def get_config():
    """Get configuration proxy."""
    return ConfigProxy()


@click.group(name="git")
def git_group():
    """Git-based library management commands."""
    pass


@git_group.command()
@click.argument("repo_url")
@click.option("--path", "-p", help="Local path for the library")
@click.option("--branch", "-b", default="main", help="Branch to clone")
def clone(repo_url: str, path: Optional[str], branch: str):
    """Clone a library repository."""
    console = Console()
    git_service = GitLibraryService(console)
    
    # Validate URL
    if not git_service.validate_repo_url(repo_url):
        console.print("❌ Invalid repository URL")
        return
    
    # Determine local path
    if path:
        local_path = Path(path).expanduser().resolve()
    else:
        config = get_config()
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        local_path = config.library_path / "remote" / repo_name
    
    # Confirm if path exists
    if local_path.exists():
        if not Confirm.ask(f"Directory {local_path} exists. Overwrite?"):
            console.print("❌ Operation cancelled")
            return
    
    # Clone repository
    success = git_service.clone_library(repo_url, local_path, branch)
    
    if success:
        # Update config with remote library path
        config = get_config()
        config.remote_library_url = repo_url
        config.remote_library_path = str(local_path)
        config.save()
        
        console.print(f"✅ Library configured at {local_path}")


@git_group.command()
@click.option("--path", "-p", help="Library path (defaults to configured remote library)")
def pull(path: Optional[str]):
    """Pull updates from remote repository."""
    console = Console()
    git_service = GitLibraryService(console)
    
    # Determine library path
    if path:
        library_path = Path(path).expanduser().resolve()
    else:
        config = get_config()
        if not config.remote_library_path:
            console.print("❌ No remote library configured. Use 'git clone' first.")
            return
        library_path = Path(config.remote_library_path)
    
    if not library_path.exists():
        console.print(f"❌ Library path does not exist: {library_path}")
        return
    
    # Pull updates
    git_service.pull_updates(library_path)


@git_group.command()
@click.option("--path", "-p", help="Library path (defaults to configured remote library)")
@click.option("--message", "-m", help="Commit message")
def push(path: Optional[str], message: Optional[str]):
    """Push local changes to remote repository."""
    console = Console()
    git_service = GitLibraryService(console)
    
    # Determine library path
    if path:
        library_path = Path(path).expanduser().resolve()
    else:
        config = get_config()
        if not config.remote_library_path:
            console.print("❌ No remote library configured. Use 'git clone' first.")
            return
        library_path = Path(config.remote_library_path)
    
    if not library_path.exists():
        console.print(f"❌ Library path does not exist: {library_path}")
        return
    
    # Get commit message
    if not message:
        message = Prompt.ask("Enter commit message", default="Update library")
    
    # Push changes
    git_service.push_changes(library_path, message)


@git_group.command()
@click.option("--path", "-p", help="Library path (defaults to configured remote library)")
def status(path: Optional[str]):
    """Show Git repository status."""
    console = Console()
    git_service = GitLibraryService(console)
    
    # Determine library path
    if path:
        library_path = Path(path).expanduser().resolve()
    else:
        config = get_config()
        if not config.remote_library_path:
            console.print("❌ No remote library configured. Use 'git clone' first.")
            return
        library_path = Path(config.remote_library_path)
    
    if not library_path.exists():
        console.print(f"❌ Library path does not exist: {library_path}")
        return
    
    # Display status
    git_service.display_status(library_path)


@git_group.command()
@click.option("--path", "-p", help="Library path (defaults to configured remote library)")
@click.option("--auto-commit", is_flag=True, help="Automatically commit local changes before sync")
def sync(path: Optional[str], auto_commit: bool):
    """Sync local library with remote repository."""
    console = Console()
    git_service = GitLibraryService(console)
    
    # Determine library path
    if path:
        library_path = Path(path).expanduser().resolve()
    else:
        config = get_config()
        if not config.remote_library_path:
            console.print("❌ No remote library configured. Use 'git clone' first.")
            return
        library_path = Path(config.remote_library_path)
    
    if not library_path.exists():
        console.print(f"❌ Library path does not exist: {library_path}")
        return
    
    # Sync with remote
    sync_history = git_service.sync_with_remote(library_path, auto_commit)
    
    if sync_history.success:
        console.print("✅ Sync completed successfully")
    else:
        console.print("❌ Sync failed. Check the output above for details.")


@git_group.command()
@click.argument("repo_url")
def configure(repo_url: str):
    """Configure remote library repository URL."""
    console = Console()
    git_service = GitLibraryService(console)
    
    # Validate URL
    if not git_service.validate_repo_url(repo_url):
        console.print("❌ Invalid repository URL")
        return
    
    # Update config
    config = get_config()
    config.remote_library_url = repo_url
    
    # Suggest default path
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    default_path = config.library_path / "remote" / repo_name
    
    path_input = Prompt.ask(
        "Enter local path for remote library",
        default=str(default_path)
    )
    
    config.remote_library_path = path_input
    config.save()
    
    console.print(f"✅ Remote library configured:")
    console.print(f"   URL: {repo_url}")
    console.print(f"   Path: {path_input}")
    console.print("\nUse 'ai-config git clone' to clone the repository.")
