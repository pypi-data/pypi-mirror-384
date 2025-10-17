"""
Value objects and enums for the AI Configurator domain.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ToolType(str, Enum):
    """Supported AI tool types."""
    Q_CLI = "q-cli"
    CLAUDE = "claude"
    CHATGPT = "chatgpt"


class LibrarySource(str, Enum):
    """Source of library files."""
    BASE = "base"
    PERSONAL = "personal"
    LOCAL = "local"


class ConflictType(str, Enum):
    """Types of library conflicts."""
    MODIFIED = "modified"
    DELETED = "deleted"
    ADDED = "added"


class Resolution(str, Enum):
    """Conflict resolution strategies."""
    KEEP_LOCAL = "keep_local"
    ACCEPT_REMOTE = "accept_remote"
    MERGE = "merge"


class SyncStatus(str, Enum):
    """Library synchronization status."""
    SYNCED = "synced"
    CONFLICTS = "conflicts"
    ERROR = "error"


class HealthStatus(str, Enum):
    """Health status for agents and servers."""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


class ResourcePath(BaseModel):
    """Reference to a knowledge file resource."""
    path: str = Field(..., description="File path relative to library root")
    source: LibrarySource = Field(..., description="Source of the file")
    
    def to_file_uri(self) -> str:
        """Convert to file:// URI format."""
        from pathlib import Path
        
        # If path is already absolute, use as-is
        if Path(self.path).is_absolute():
            return f"file://{self.path}"
        
        # For relative paths, resolve based on source
        if self.source == LibrarySource.BASE:
            from ai_configurator.tui.config import get_library_paths
            base_path, _ = get_library_paths()
            full_path = base_path / self.path
            return f"file://{full_path}"
        elif self.source == LibrarySource.PERSONAL:
            from ai_configurator.tui.config import get_library_paths
            _, personal_path = get_library_paths()
            full_path = personal_path / self.path
            return f"file://{full_path}"
        else:
            # Fallback to relative path
            return f"file://{self.path}"
    
    class Config:
        frozen = True
