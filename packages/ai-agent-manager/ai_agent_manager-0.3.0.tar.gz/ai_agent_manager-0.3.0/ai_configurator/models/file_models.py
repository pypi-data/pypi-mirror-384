"""
File management models for local file discovery and monitoring.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

from .value_objects import LibrarySource


class FilePattern(BaseModel):
    """Represents a glob pattern for file discovery."""
    pattern: str = Field(..., description="Glob pattern (e.g., './rules/**/*.md')")
    base_path: Path = Field(..., description="Base path for pattern resolution")
    recursive: bool = Field(default=True, description="Whether pattern is recursive")
    file_extensions: Set[str] = Field(default_factory=lambda: {".md"}, description="Allowed file extensions")
    exclude_patterns: List[str] = Field(default_factory=list, description="Patterns to exclude")
    
    def resolve_pattern(self) -> str:
        """Resolve pattern relative to base path."""
        if self.pattern.startswith('./'):
            return str(self.base_path / self.pattern[2:])
        elif self.pattern.startswith('/'):
            return self.pattern
        else:
            return str(self.base_path / self.pattern)
    
    def matches_extension(self, file_path: Path) -> bool:
        """Check if file extension is allowed."""
        return file_path.suffix.lower() in self.file_extensions
    
    def is_excluded(self, file_path: Path) -> bool:
        """Check if file matches any exclude pattern."""
        file_str = str(file_path)
        return any(
            file_path.match(exclude_pattern) 
            for exclude_pattern in self.exclude_patterns
        )


class LocalResource(BaseModel):
    """Represents a local file resource with change tracking."""
    file_path: Path = Field(..., description="Absolute path to the file")
    relative_path: str = Field(..., description="Path relative to agent or project root")
    content_hash: str = Field(..., description="Hash of file content")
    last_modified: datetime = Field(..., description="Last modification time")
    size_bytes: int = Field(..., description="File size in bytes")
    source: LibrarySource = Field(default=LibrarySource.LOCAL, description="Source type")
    watched: bool = Field(default=False, description="Whether file is being watched")
    
    def needs_update(self, current_mtime: datetime, current_hash: str) -> bool:
        """Check if resource needs updating."""
        return (
            current_mtime > self.last_modified or 
            current_hash != self.content_hash
        )
    
    def update_metadata(self, mtime: datetime, content_hash: str, size: int) -> None:
        """Update resource metadata."""
        self.last_modified = mtime
        self.content_hash = content_hash
        self.size_bytes = size


class FileWatchConfig(BaseModel):
    """Configuration for file watching."""
    enabled: bool = Field(default=True, description="Whether watching is enabled")
    patterns: List[FilePattern] = Field(default_factory=list, description="Patterns to watch")
    debounce_seconds: float = Field(default=1.0, description="Debounce time for file changes")
    max_files: int = Field(default=1000, description="Maximum files to watch")
    auto_add_new_files: bool = Field(default=True, description="Automatically add new matching files")


class FileDiscoveryResult(BaseModel):
    """Result of file discovery operation."""
    discovered_files: List[Path] = Field(default_factory=list, description="Files found")
    total_files: int = Field(default=0, description="Total files discovered")
    matched_patterns: Dict[str, int] = Field(default_factory=dict, description="Files per pattern")
    excluded_files: List[Path] = Field(default_factory=list, description="Files excluded")
    errors: List[str] = Field(default_factory=list, description="Discovery errors")
    
    def add_file(self, file_path: Path, pattern: str) -> None:
        """Add a discovered file."""
        self.discovered_files.append(file_path)
        self.total_files += 1
        self.matched_patterns[pattern] = self.matched_patterns.get(pattern, 0) + 1
    
    def add_excluded(self, file_path: Path) -> None:
        """Add an excluded file."""
        self.excluded_files.append(file_path)
    
    def add_error(self, error: str) -> None:
        """Add a discovery error."""
        self.errors.append(error)


class FileWatcher(BaseModel):
    """Manages file system monitoring for local resources."""
    agent_id: str = Field(..., description="ID of the agent being watched")
    watch_config: FileWatchConfig = Field(..., description="Watch configuration")
    watched_files: Dict[str, LocalResource] = Field(default_factory=dict, description="Currently watched files")
    last_scan: Optional[datetime] = Field(default=None, description="Last scan timestamp")
    is_active: bool = Field(default=False, description="Whether watcher is active")
    
    def add_file(self, resource: LocalResource) -> None:
        """Add a file to watch list."""
        key = str(resource.file_path)
        self.watched_files[key] = resource
        resource.watched = True
    
    def remove_file(self, file_path: Path) -> bool:
        """Remove a file from watch list."""
        key = str(file_path)
        if key in self.watched_files:
            self.watched_files[key].watched = False
            del self.watched_files[key]
            return True
        return False
    
    def get_file(self, file_path: Path) -> Optional[LocalResource]:
        """Get watched file resource."""
        key = str(file_path)
        return self.watched_files.get(key)
    
    def update_file(self, file_path: Path, mtime: datetime, content_hash: str, size: int) -> bool:
        """Update file metadata if it's being watched."""
        resource = self.get_file(file_path)
        if resource:
            resource.update_metadata(mtime, content_hash, size)
            return True
        return False
    
    def get_stale_files(self) -> List[LocalResource]:
        """Get files that may need updating."""
        stale = []
        for resource in self.watched_files.values():
            if resource.file_path.exists():
                current_mtime = datetime.fromtimestamp(resource.file_path.stat().st_mtime)
                if current_mtime > resource.last_modified:
                    stale.append(resource)
        return stale
