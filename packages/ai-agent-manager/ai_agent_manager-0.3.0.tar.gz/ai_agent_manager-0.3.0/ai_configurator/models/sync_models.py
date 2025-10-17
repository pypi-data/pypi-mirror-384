"""
Synchronization models for library management.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from .value_objects import ConflictType, Resolution, SyncStatus


class FileDiff(BaseModel):
    """Represents differences between two file versions."""
    file_path: str = Field(..., description="Path to the file")
    base_content: str = Field(default="", description="Base library content")
    personal_content: str = Field(default="", description="Personal library content")
    diff_lines: List[str] = Field(default_factory=list, description="Unified diff lines")
    
    class Config:
        frozen = True


class ConflictReport(BaseModel):
    """Detailed report of a synchronization conflict."""
    file_path: str = Field(..., description="Path to conflicted file")
    conflict_type: ConflictType = Field(..., description="Type of conflict")
    base_exists: bool = Field(..., description="File exists in base library")
    personal_exists: bool = Field(..., description="File exists in personal library")
    base_hash: str = Field(default="", description="Hash of base content")
    personal_hash: str = Field(default="", description="Hash of personal content")
    diff: Optional[FileDiff] = Field(default=None, description="File differences")
    suggested_resolution: Resolution = Field(..., description="Suggested resolution")
    
    def is_safe_merge(self) -> bool:
        """Check if this conflict can be safely auto-merged."""
        return (
            self.conflict_type == ConflictType.MODIFIED and
            self.base_exists and 
            self.personal_exists and
            self.suggested_resolution == Resolution.MERGE
        )


class SyncOperation(BaseModel):
    """Represents a single sync operation."""
    file_path: str = Field(..., description="Path to the file")
    operation: str = Field(..., description="Operation type: add, update, delete, resolve")
    resolution: Optional[Resolution] = Field(default=None, description="Applied resolution")
    backup_path: Optional[str] = Field(default=None, description="Path to backup file")
    success: bool = Field(default=False, description="Operation success status")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class SyncHistory(BaseModel):
    """History of synchronization operations."""
    timestamp: datetime = Field(default_factory=datetime.now)
    base_version: str = Field(..., description="Base library version")
    personal_version: str = Field(..., description="Personal library version")
    operations: List[SyncOperation] = Field(default_factory=list)
    conflicts_detected: int = Field(default=0, description="Number of conflicts detected")
    conflicts_resolved: int = Field(default=0, description="Number of conflicts resolved")
    success: bool = Field(default=False, description="Overall sync success")
    
    def add_operation(self, operation: SyncOperation) -> None:
        """Add an operation to the history."""
        self.operations.append(operation)


class LibrarySync(BaseModel):
    """Manages library synchronization state and operations."""
    base_path: Path = Field(..., description="Path to base library")
    personal_path: Path = Field(..., description="Path to personal library")
    backup_path: Path = Field(..., description="Path to backup directory")
    current_conflicts: List[ConflictReport] = Field(default_factory=list)
    sync_history: List[SyncHistory] = Field(default_factory=list)
    last_sync: Optional[datetime] = Field(default=None, description="Last sync timestamp")
    
    def add_conflict(self, conflict: ConflictReport) -> None:
        """Add a new conflict to the current list."""
        # Remove existing conflict for the same file
        self.current_conflicts = [
            c for c in self.current_conflicts 
            if c.file_path != conflict.file_path
        ]
        self.current_conflicts.append(conflict)
    
    def resolve_conflict(self, file_path: str, resolution: Resolution) -> bool:
        """Mark a conflict as resolved."""
        for i, conflict in enumerate(self.current_conflicts):
            if conflict.file_path == file_path:
                # Remove the resolved conflict
                self.current_conflicts.pop(i)
                return True
        return False
    
    def has_conflicts(self) -> bool:
        """Check if there are unresolved conflicts."""
        return len(self.current_conflicts) > 0
    
    def get_conflict(self, file_path: str) -> Optional[ConflictReport]:
        """Get conflict report for a specific file."""
        for conflict in self.current_conflicts:
            if conflict.file_path == file_path:
                return conflict
        return None
    
    def create_backup_name(self) -> str:
        """Generate a backup directory name."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}"
