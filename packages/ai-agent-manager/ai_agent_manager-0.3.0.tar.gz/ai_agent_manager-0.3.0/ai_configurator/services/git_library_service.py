"""
Git-based library management service.
"""

import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

try:
    import git
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

from ..models.sync_models import SyncHistory, SyncOperation
from ..models.value_objects import Resolution


class GitLibraryService:
    """Service for Git-based library management."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        if not GIT_AVAILABLE:
            raise ImportError("GitPython is required. Install with: pip install gitpython")
    
    def clone_library(self, repo_url: str, local_path: Path, branch: str = "main") -> bool:
        """Clone a library repository."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task(f"Cloning {repo_url}...", total=None)
                
                if local_path.exists():
                    shutil.rmtree(local_path)
                
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                repo = Repo.clone_from(repo_url, local_path, branch=branch)
                progress.update(task, completed=True)
                
            self.console.print(f"✅ Library cloned to {local_path}")
            return True
            
        except GitCommandError as e:
            self.console.print(f"❌ Failed to clone repository: {e}")
            return False
        except Exception as e:
            self.console.print(f"❌ Unexpected error: {e}")
            return False
    
    def pull_updates(self, local_path: Path) -> bool:
        """Pull updates from remote repository."""
        try:
            if not self._is_git_repo(local_path):
                self.console.print(f"❌ {local_path} is not a Git repository")
                return False
            
            repo = Repo(local_path)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Pulling updates...", total=None)
                
                origin = repo.remotes.origin
                origin.pull()
                progress.update(task, completed=True)
            
            self.console.print("✅ Updates pulled successfully")
            return True
            
        except GitCommandError as e:
            self.console.print(f"❌ Failed to pull updates: {e}")
            return False
        except Exception as e:
            self.console.print(f"❌ Unexpected error: {e}")
            return False
    
    def push_changes(self, local_path: Path, message: str = "Update library") -> bool:
        """Push local changes to remote repository."""
        try:
            if not self._is_git_repo(local_path):
                self.console.print(f"❌ {local_path} is not a Git repository")
                return False
            
            repo = Repo(local_path)
            
            # Check if there are changes to commit
            if not repo.is_dirty() and not repo.untracked_files:
                self.console.print("ℹ️  No changes to push")
                return True
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Pushing changes...", total=None)
                
                # Add all changes
                repo.git.add(A=True)
                
                # Commit changes
                repo.index.commit(message)
                
                # Push to remote
                origin = repo.remotes.origin
                origin.push()
                progress.update(task, completed=True)
            
            self.console.print("✅ Changes pushed successfully")
            return True
            
        except GitCommandError as e:
            self.console.print(f"❌ Failed to push changes: {e}")
            return False
        except Exception as e:
            self.console.print(f"❌ Unexpected error: {e}")
            return False
    
    def get_status(self, local_path: Path) -> Dict[str, Any]:
        """Get Git repository status."""
        if not self._is_git_repo(local_path):
            return {"error": "Not a Git repository"}
        
        try:
            repo = Repo(local_path)
            
            # Get remote info
            remote_url = None
            if repo.remotes:
                remote_url = repo.remotes.origin.url
            
            # Get current branch
            current_branch = repo.active_branch.name if repo.active_branch else "detached"
            
            # Get commit info
            latest_commit = repo.head.commit
            
            # Check for changes
            has_changes = repo.is_dirty() or bool(repo.untracked_files)
            
            return {
                "remote_url": remote_url,
                "current_branch": current_branch,
                "latest_commit": {
                    "hash": latest_commit.hexsha[:8],
                    "message": latest_commit.message.strip(),
                    "author": str(latest_commit.author),
                    "date": latest_commit.committed_datetime.isoformat()
                },
                "has_changes": has_changes,
                "modified_files": list(repo.git.diff("--name-only").splitlines()),
                "untracked_files": repo.untracked_files
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def display_status(self, local_path: Path) -> None:
        """Display repository status in a user-friendly format."""
        status = self.get_status(local_path)
        
        if "error" in status:
            self.console.print(f"❌ {status['error']}")
            return
        
        # Create status panel
        status_lines = []
        status_lines.append(f"📁 Repository: {local_path}")
        
        if status["remote_url"]:
            status_lines.append(f"🌐 Remote: {status['remote_url']}")
        
        status_lines.append(f"🌿 Branch: {status['current_branch']}")
        
        commit = status["latest_commit"]
        status_lines.append(f"📝 Latest: {commit['hash']} - {commit['message']}")
        status_lines.append(f"👤 Author: {commit['author']}")
        
        if status["has_changes"]:
            status_lines.append("⚠️  Has uncommitted changes")
            if status["modified_files"]:
                status_lines.append(f"   Modified: {', '.join(status['modified_files'])}")
            if status["untracked_files"]:
                status_lines.append(f"   Untracked: {', '.join(status['untracked_files'])}")
        else:
            status_lines.append("✅ Working directory clean")
        
        panel = Panel(
            "\n".join(status_lines),
            title="Git Repository Status",
            border_style="blue"
        )
        self.console.print(panel)
    
    def sync_with_remote(self, local_path: Path, auto_commit: bool = False) -> SyncHistory:
        """Sync local library with remote repository."""
        sync_history = SyncHistory(
            base_version="remote",
            personal_version="local"
        )
        
        try:
            if not self._is_git_repo(local_path):
                self.console.print(f"❌ {local_path} is not a Git repository")
                sync_history.success = False
                return sync_history
            
            repo = Repo(local_path)
            
            # Check for local changes
            has_changes = repo.is_dirty() or bool(repo.untracked_files)
            
            if has_changes and auto_commit:
                # Auto-commit local changes
                operation = SyncOperation(
                    file_path="*",
                    operation="commit",
                    resolution=Resolution.KEEP_LOCAL
                )
                
                try:
                    repo.git.add(A=True)
                    repo.index.commit("Auto-commit local changes before sync")
                    operation.success = True
                    sync_history.add_operation(operation)
                except Exception as e:
                    operation.error_message = str(e)
                    operation.success = False
                    sync_history.add_operation(operation)
                    sync_history.success = False
                    return sync_history
            
            # Pull updates
            pull_operation = SyncOperation(
                file_path="*",
                operation="pull",
                resolution=Resolution.ACCEPT_REMOTE
            )
            
            try:
                origin = repo.remotes.origin
                origin.pull()
                pull_operation.success = True
                sync_history.add_operation(pull_operation)
                sync_history.success = True
                
            except GitCommandError as e:
                if "merge conflict" in str(e).lower():
                    self.console.print("⚠️  Merge conflicts detected. Manual resolution required.")
                    pull_operation.error_message = "Merge conflicts require manual resolution"
                else:
                    pull_operation.error_message = str(e)
                
                pull_operation.success = False
                sync_history.add_operation(pull_operation)
                sync_history.success = False
            
        except Exception as e:
            self.console.print(f"❌ Sync failed: {e}")
            sync_history.success = False
        
        return sync_history
    
    def _is_git_repo(self, path: Path) -> bool:
        """Check if path is a Git repository."""
        try:
            Repo(path)
            return True
        except:
            return False
    
    def validate_repo_url(self, url: str) -> bool:
        """Validate if URL is a valid Git repository URL."""
        try:
            parsed = urlparse(url)
            
            # Check for common Git URL patterns
            if parsed.scheme in ['http', 'https', 'git', 'ssh']:
                return True
            
            # Check for SSH format (git@host:repo.git)
            if '@' in url and ':' in url:
                return True
            
            return False
            
        except Exception:
            return False
