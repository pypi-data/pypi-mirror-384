"""
Library synchronization service.
"""

import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from ..models.sync_models import (
    ConflictReport, FileDiff, LibrarySync, SyncHistory, SyncOperation
)
from ..models.value_objects import ConflictType, Resolution
from ..models.library import Library, LibraryMetadata


class SyncService:
    """Service for managing library synchronization."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        if not file_path.exists():
            return ""
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def generate_diff(self, base_content: str, personal_content: str, file_path: str) -> FileDiff:
        """Generate diff between base and personal content."""
        import difflib
        
        base_lines = base_content.splitlines(keepends=True)
        personal_lines = personal_content.splitlines(keepends=True)
        
        diff_lines = list(difflib.unified_diff(
            base_lines, 
            personal_lines,
            fromfile=f"base/{file_path}",
            tofile=f"personal/{file_path}",
            lineterm=""
        ))
        
        return FileDiff(
            file_path=file_path,
            base_content=base_content,
            personal_content=personal_content,
            diff_lines=diff_lines
        )
    
    def detect_conflicts(self, library_sync: LibrarySync) -> List[ConflictReport]:
        """Detect conflicts between base and personal libraries."""
        conflicts = []
        
        # Get all files from both libraries
        base_files = self._scan_directory(library_sync.base_path)
        personal_files = self._scan_directory(library_sync.personal_path)
        
        all_files = set(base_files.keys()) | set(personal_files.keys())
        
        for file_path in all_files:
            base_info = base_files.get(file_path)
            personal_info = personal_files.get(file_path)
            
            conflict = self._analyze_file_conflict(
                file_path, base_info, personal_info, library_sync
            )
            
            if conflict:
                conflicts.append(conflict)
        
        return conflicts
    
    def _scan_directory(self, directory: Path) -> Dict[str, Tuple[Path, str]]:
        """Scan directory and return file info."""
        files = {}
        
        if not directory.exists():
            return files
        
        for file_path in directory.rglob("*.md"):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(directory))
                file_hash = self.calculate_file_hash(file_path)
                files[relative_path] = (file_path, file_hash)
        
        return files
    
    def _analyze_file_conflict(
        self, 
        file_path: str, 
        base_info: Optional[Tuple[Path, str]], 
        personal_info: Optional[Tuple[Path, str]],
        library_sync: LibrarySync
    ) -> Optional[ConflictReport]:
        """Analyze a single file for conflicts."""
        base_exists = base_info is not None
        personal_exists = personal_info is not None
        
        # No conflict if file exists in only one location
        if not base_exists and personal_exists:
            return None  # Personal addition, no conflict
        
        if base_exists and not personal_exists:
            return None  # Base addition, no conflict
        
        # Both exist - check for modifications
        if base_exists and personal_exists:
            base_path, base_hash = base_info
            personal_path, personal_hash = personal_info
            
            if base_hash == personal_hash:
                return None  # No changes, no conflict
            
            # Files differ - create conflict report
            base_content = base_path.read_text(encoding='utf-8')
            personal_content = personal_path.read_text(encoding='utf-8')
            
            diff = self.generate_diff(base_content, personal_content, file_path)
            
            return ConflictReport(
                file_path=file_path,
                conflict_type=ConflictType.MODIFIED,
                base_exists=True,
                personal_exists=True,
                base_hash=base_hash,
                personal_hash=personal_hash,
                diff=diff,
                suggested_resolution=Resolution.KEEP_LOCAL  # Default to keeping personal changes
            )
        
        return None
    
    def create_backup(self, library_sync: LibrarySync) -> Path:
        """Create backup of personal library before sync."""
        backup_name = library_sync.create_backup_name()
        backup_dir = library_sync.backup_path / backup_name
        
        if library_sync.personal_path.exists():
            shutil.copytree(library_sync.personal_path, backup_dir)
            self.console.print(f"✅ Backup created: {backup_dir}")
        
        return backup_dir
    
    def display_conflicts(self, conflicts: List[ConflictReport]) -> None:
        """Display conflicts in a user-friendly format."""
        if not conflicts:
            self.console.print("✅ No conflicts detected!")
            return
        
        self.console.print(f"\n⚠️  Found {len(conflicts)} conflicts:")
        
        table = Table(title="Library Conflicts")
        table.add_column("File", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Suggested Resolution", style="green")
        
        for conflict in conflicts:
            table.add_row(
                conflict.file_path,
                conflict.conflict_type.value,
                conflict.suggested_resolution.value
            )
        
        self.console.print(table)
    
    def display_diff(self, conflict: ConflictReport) -> None:
        """Display diff for a specific conflict."""
        if not conflict.diff:
            return
        
        self.console.print(f"\n📄 Diff for {conflict.file_path}:")
        
        diff_text = "\n".join(conflict.diff.diff_lines)
        panel = Panel(diff_text, title="File Differences", border_style="blue")
        self.console.print(panel)
    
    def resolve_conflict_interactive(self, conflict: ConflictReport) -> Resolution:
        """Interactively resolve a single conflict."""
        self.console.print(f"\n🔧 Resolving conflict: {conflict.file_path}")
        
        # Show diff
        self.display_diff(conflict)
        
        # Get user choice
        choices = {
            "1": Resolution.KEEP_LOCAL,
            "2": Resolution.ACCEPT_REMOTE,
            "3": Resolution.MERGE
        }
        
        self.console.print("\nResolution options:")
        self.console.print("1. Keep local (personal) version")
        self.console.print("2. Accept remote (base) version")
        self.console.print("3. Manual merge (open editor)")
        
        while True:
            choice = Prompt.ask("Choose resolution", choices=list(choices.keys()))
            if choice in choices:
                return choices[choice]
    
    def apply_resolution(
        self, 
        conflict: ConflictReport, 
        resolution: Resolution,
        library_sync: LibrarySync
    ) -> SyncOperation:
        """Apply a conflict resolution."""
        operation = SyncOperation(
            file_path=conflict.file_path,
            operation="resolve",
            resolution=resolution
        )
        
        try:
            personal_file = library_sync.personal_path / conflict.file_path
            base_file = library_sync.base_path / conflict.file_path
            
            if resolution == Resolution.KEEP_LOCAL:
                # Keep personal version - no action needed
                operation.success = True
                
            elif resolution == Resolution.ACCEPT_REMOTE:
                # Copy base version to personal
                personal_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(base_file, personal_file)
                operation.success = True
                
            elif resolution == Resolution.MERGE:
                # Open editor for manual merge
                self._open_merge_editor(base_file, personal_file)
                operation.success = True
            
        except Exception as e:
            operation.error_message = str(e)
            operation.success = False
        
        return operation
    
    def _open_merge_editor(self, base_file: Path, personal_file: Path) -> None:
        """Open external editor for manual merge."""
        import subprocess
        import os
        
        # Try different editors
        editors = ['code', 'vim', 'nano', 'gedit']
        
        for editor in editors:
            try:
                if editor == 'code':
                    # VS Code with diff view
                    subprocess.run([editor, '--diff', str(base_file), str(personal_file)])
                else:
                    subprocess.run([editor, str(personal_file)])
                break
            except FileNotFoundError:
                continue
        else:
            self.console.print("⚠️  No suitable editor found. Please manually edit the file.")
    
    def sync_library(self, library_sync: LibrarySync, interactive: bool = True) -> SyncHistory:
        """Perform library synchronization."""
        sync_history = SyncHistory(
            base_version="latest",  # TODO: Implement proper versioning
            personal_version="current"
        )
        
        try:
            # Create backup
            backup_dir = self.create_backup(library_sync)
            
            # Detect conflicts
            conflicts = self.detect_conflicts(library_sync)
            sync_history.conflicts_detected = len(conflicts)
            
            if not conflicts:
                self.console.print("✅ No conflicts found. Library is up to date!")
                sync_history.success = True
                return sync_history
            
            # Display conflicts
            self.display_conflicts(conflicts)
            
            if not interactive:
                self.console.print("⚠️  Conflicts detected but running in non-interactive mode.")
                sync_history.success = False
                return sync_history
            
            # Resolve conflicts interactively
            for conflict in conflicts:
                resolution = self.resolve_conflict_interactive(conflict)
                operation = self.apply_resolution(conflict, resolution, library_sync)
                sync_history.add_operation(operation)
                
                if operation.success:
                    sync_history.conflicts_resolved += 1
                    library_sync.resolve_conflict(conflict.file_path, resolution)
            
            sync_history.success = sync_history.conflicts_resolved == sync_history.conflicts_detected
            
            if sync_history.success:
                self.console.print("✅ All conflicts resolved successfully!")
            else:
                self.console.print("⚠️  Some conflicts could not be resolved.")
            
        except Exception as e:
            self.console.print(f"❌ Sync failed: {e}")
            sync_history.success = False
        
        return sync_history
