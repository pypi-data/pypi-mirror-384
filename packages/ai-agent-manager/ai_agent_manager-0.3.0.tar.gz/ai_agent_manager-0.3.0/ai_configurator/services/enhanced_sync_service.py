"""
Enhanced library synchronization service with Git support.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt

from .git_library_service import GitLibraryService
from .sync_service import SyncService
from ..models.sync_models import LibrarySync, SyncHistory, ConflictReport
from ..models.value_objects import Resolution
from ..core.config import ConfigProxy


class EnhancedSyncService:
    """Enhanced synchronization service supporting both local and Git-based libraries."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.git_service = GitLibraryService(console)
        self.local_sync_service = SyncService(console)
        self.config = ConfigProxy()
    
    def sync_all_libraries(self, interactive: bool = True) -> Dict[str, SyncHistory]:
        """Sync all configured libraries (local and remote)."""
        results = {}
        
        # Sync local libraries (existing functionality)
        local_sync = self._sync_local_libraries(interactive)
        if local_sync:
            results["local"] = local_sync
        
        # Sync remote Git libraries
        remote_sync = self._sync_remote_libraries(interactive)
        if remote_sync:
            results["remote"] = remote_sync
        
        return results
    
    def _sync_local_libraries(self, interactive: bool) -> Optional[SyncHistory]:
        """Sync local base and personal libraries."""
        try:
            library_sync = LibrarySync(
                base_path=Path(self.config.library_path),
                personal_path=Path(self.config._config.library_config.personal_library_path),
                backup_path=Path(self.config._config.library_config.backup_path)
            )
            
            return self.local_sync_service.sync_library(library_sync, interactive)
            
        except Exception as e:
            self.console.print(f"❌ Local library sync failed: {e}")
            return None
    
    def _sync_remote_libraries(self, interactive: bool) -> Optional[SyncHistory]:
        """Sync remote Git-based libraries."""
        if not self.config.remote_library_url or not self.config.remote_library_path:
            self.console.print("ℹ️  No remote library configured")
            return None
        
        try:
            remote_path = Path(self.config.remote_library_path)
            
            # Check if remote library exists locally
            if not remote_path.exists():
                if interactive and Confirm.ask(f"Remote library not found locally. Clone from {self.config.remote_library_url}?"):
                    success = self.git_service.clone_library(
                        self.config.remote_library_url,
                        remote_path
                    )
                    if not success:
                        return None
                else:
                    self.console.print("❌ Remote library not available locally")
                    return None
            
            # Sync with remote
            return self.git_service.sync_with_remote(remote_path, auto_commit=False)
            
        except Exception as e:
            self.console.print(f"❌ Remote library sync failed: {e}")
            return None
    
    def configure_remote_library(self, repo_url: str, local_path: Optional[str] = None) -> bool:
        """Configure a remote Git library."""
        if not self.git_service.validate_repo_url(repo_url):
            self.console.print("❌ Invalid repository URL")
            return False
        
        # Determine local path
        if not local_path:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            local_path = str(self.config.library_path / "remote" / repo_name)
        
        # Update configuration
        self.config.remote_library_url = repo_url
        self.config.remote_library_path = local_path
        self.config.save()
        
        self.console.print(f"✅ Remote library configured:")
        self.console.print(f"   URL: {repo_url}")
        self.console.print(f"   Local path: {local_path}")
        
        return True
    
    def list_library_sources(self) -> None:
        """List all configured library sources."""
        table = Table(title="Library Sources")
        table.add_column("Type", style="cyan")
        table.add_column("Path/URL", style="white")
        table.add_column("Status", style="green")
        
        # Local libraries
        local_base = Path(self.config.library_path)
        local_personal = Path(self.config._config.library_config.personal_library_path)
        
        table.add_row(
            "Local Base",
            str(local_base),
            "✅ Available" if local_base.exists() else "❌ Missing"
        )
        
        table.add_row(
            "Local Personal",
            str(local_personal),
            "✅ Available" if local_personal.exists() else "❌ Missing"
        )
        
        # Remote library
        if self.config.remote_library_url:
            remote_path = Path(self.config.remote_library_path) if self.config.remote_library_path else None
            status = "❌ Not cloned"
            
            if remote_path and remote_path.exists():
                if self.git_service._is_git_repo(remote_path):
                    git_status = self.git_service.get_status(remote_path)
                    if "error" not in git_status:
                        status = "✅ Available (Git)"
                        if git_status.get("has_changes"):
                            status += " 🔄 Has changes"
                    else:
                        status = "⚠️  Git error"
                else:
                    status = "⚠️  Not a Git repo"
            
            table.add_row(
                "Remote Git",
                f"{self.config.remote_library_url}\n→ {self.config.remote_library_path}",
                status
            )
        else:
            table.add_row(
                "Remote Git",
                "Not configured",
                "➖ N/A"
            )
        
        self.console.print(table)
    
    def sync_specific_source(self, source_type: str, interactive: bool = True) -> Optional[SyncHistory]:
        """Sync a specific library source."""
        if source_type == "local":
            return self._sync_local_libraries(interactive)
        elif source_type == "remote":
            return self._sync_remote_libraries(interactive)
        else:
            self.console.print(f"❌ Unknown source type: {source_type}")
            return None
    
    def get_library_status(self) -> Dict[str, Dict]:
        """Get status of all library sources."""
        status = {}
        
        # Local libraries
        local_base = Path(self.config.library_path)
        local_personal = Path(self.config._config.library_config.personal_library_path)
        
        status["local"] = {
            "base_path": str(local_base),
            "personal_path": str(local_personal),
            "base_exists": local_base.exists(),
            "personal_exists": local_personal.exists(),
            "base_files": len(list(local_base.rglob("*.md"))) if local_base.exists() else 0,
            "personal_files": len(list(local_personal.rglob("*.md"))) if local_personal.exists() else 0
        }
        
        # Remote library
        if self.config.remote_library_url and self.config.remote_library_path:
            remote_path = Path(self.config.remote_library_path)
            git_status = self.git_service.get_status(remote_path) if remote_path.exists() else {"error": "Not cloned"}
            
            status["remote"] = {
                "url": self.config.remote_library_url,
                "local_path": str(remote_path),
                "exists": remote_path.exists(),
                "is_git_repo": self.git_service._is_git_repo(remote_path) if remote_path.exists() else False,
                "git_status": git_status,
                "files": len(list(remote_path.rglob("*.md"))) if remote_path.exists() else 0
            }
        else:
            status["remote"] = {
                "configured": False
            }
        
        return status
    
    def display_sync_summary(self, results: Dict[str, SyncHistory]) -> None:
        """Display a summary of sync results."""
        if not results:
            self.console.print("ℹ️  No sync operations performed")
            return
        
        summary_lines = []
        overall_success = True
        
        for source, history in results.items():
            if history.success:
                summary_lines.append(f"✅ {source.title()}: {history.conflicts_resolved}/{history.conflicts_detected} conflicts resolved")
            else:
                summary_lines.append(f"❌ {source.title()}: Sync failed")
                overall_success = False
        
        panel_style = "green" if overall_success else "red"
        title = "Sync Summary - Success" if overall_success else "Sync Summary - Issues Found"
        
        panel = Panel(
            "\n".join(summary_lines),
            title=title,
            border_style=panel_style
        )
        
        self.console.print(panel)
    
    def resolve_conflicts_interactive(self, conflicts: List[ConflictReport], library_sync: LibrarySync) -> List[bool]:
        """Interactively resolve multiple conflicts."""
        results = []
        
        if not conflicts:
            return results
        
        self.console.print(f"\n⚠️  Found {len(conflicts)} conflicts to resolve:")
        
        for i, conflict in enumerate(conflicts, 1):
            self.console.print(f"\n[bold]Conflict {i}/{len(conflicts)}:[/bold] {conflict.file_path}")
            
            resolution = self.local_sync_service.resolve_conflict_interactive(conflict)
            operation = self.local_sync_service.apply_resolution(conflict, resolution, library_sync)
            
            results.append(operation.success)
            
            if operation.success:
                self.console.print(f"✅ Resolved: {resolution.value}")
            else:
                self.console.print(f"❌ Failed: {operation.error_message}")
        
        return results
