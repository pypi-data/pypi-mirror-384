"""
Library domain model for knowledge management.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .value_objects import LibrarySource, ConflictType, Resolution, SyncStatus


class ConflictInfo(BaseModel):
    """Information about a library synchronization conflict."""
    file_path: str = Field(..., description="Path to conflicted file")
    base_content_hash: str = Field(..., description="Hash of base library content")
    personal_content_hash: str = Field(..., description="Hash of personal library content")
    conflict_type: ConflictType = Field(..., description="Type of conflict")
    resolution: Optional[Resolution] = Field(default=None, description="Applied resolution")
    
    class Config:
        frozen = True


class LibraryMetadata(BaseModel):
    """Metadata for library synchronization and versioning."""
    version: str = Field(..., description="Library version")
    last_sync: datetime = Field(default_factory=datetime.now)
    base_hash: str = Field(default="", description="Hash of base library state")
    personal_hash: str = Field(default="", description="Hash of personal library state")
    conflicts: List[ConflictInfo] = Field(default_factory=list)
    sync_status: SyncStatus = Field(default=SyncStatus.SYNCED)


class LibraryFile(BaseModel):
    """Represents a file in the knowledge library."""
    path: str = Field(..., description="Relative path from library root")
    source: LibrarySource = Field(..., description="Source of the file")
    content_hash: str = Field(..., description="Hash of file content")
    last_modified: datetime = Field(default_factory=datetime.now)
    size: int = Field(default=0, description="File size in bytes")


class Library(BaseModel):
    """Core Library domain entity."""
    base_path: Path = Field(..., description="Path to base library")
    personal_path: Path = Field(..., description="Path to personal library")
    metadata: LibraryMetadata = Field(default_factory=LibraryMetadata)
    files: Dict[str, LibraryFile] = Field(default_factory=dict)
    
    def get_effective_file(self, relative_path: str) -> Optional[LibraryFile]:
        """Get effective file with personal library taking precedence."""
        # Check personal library first
        personal_key = f"personal/{relative_path}"
        if personal_key in self.files:
            return self.files[personal_key]
        
        # Fall back to base library
        base_key = f"base/{relative_path}"
        return self.files.get(base_key)
    
    def has_conflict(self, relative_path: str) -> bool:
        """Check if a file has unresolved conflicts."""
        return any(
            conflict.file_path == relative_path and conflict.resolution is None
            for conflict in self.metadata.conflicts
        )
    
    def add_conflict(self, conflict: ConflictInfo) -> None:
        """Add a new conflict to the metadata."""
        # Remove existing conflict for the same file
        self.metadata.conflicts = [
            c for c in self.metadata.conflicts 
            if c.file_path != conflict.file_path
        ]
        self.metadata.conflicts.append(conflict)
        self.metadata.sync_status = SyncStatus.CONFLICTS
    
    def resolve_conflict(self, file_path: str, resolution: Resolution) -> bool:
        """Resolve a conflict for a specific file."""
        for conflict in self.metadata.conflicts:
            if conflict.file_path == file_path and conflict.resolution is None:
                # Create new conflict with resolution (since ConflictInfo is frozen)
                resolved_conflict = ConflictInfo(
                    file_path=conflict.file_path,
                    base_content_hash=conflict.base_content_hash,
                    personal_content_hash=conflict.personal_content_hash,
                    conflict_type=conflict.conflict_type,
                    resolution=resolution
                )
                
                # Replace the conflict
                self.metadata.conflicts = [
                    c if c.file_path != file_path else resolved_conflict
                    for c in self.metadata.conflicts
                ]
                
                # Update sync status if all conflicts resolved
                unresolved = [c for c in self.metadata.conflicts if c.resolution is None]
                if not unresolved:
                    self.metadata.sync_status = SyncStatus.SYNCED
                
                return True
        return False
    
    def discover_files(self, pattern: str = "**/*.md") -> List[str]:
        """Discover files matching the given pattern."""
        discovered = []
        
        # Search base library
        if self.base_path.exists():
            for file_path in self.base_path.glob(pattern):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.base_path)
                    discovered.append(str(relative_path))
        
        # Search personal library (overrides base)
        if self.personal_path.exists():
            for file_path in self.personal_path.glob(pattern):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.personal_path)
                    discovered.append(str(relative_path))
        
        return list(set(discovered))  # Remove duplicates
