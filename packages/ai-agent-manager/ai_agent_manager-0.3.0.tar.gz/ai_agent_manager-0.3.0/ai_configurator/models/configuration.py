"""
Configuration domain model for user preferences and system settings.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .value_objects import ToolType


class BackupPolicy(BaseModel):
    """Backup retention and creation policy."""
    auto_backup_before_operations: bool = Field(default=True)
    max_daily_backups: int = Field(default=7, ge=1)
    max_operation_backups: int = Field(default=10, ge=1)
    backup_retention_days: int = Field(default=30, ge=1)


class SyncSettings(BaseModel):
    """Library synchronization preferences."""
    auto_sync_on_startup: bool = Field(default=True)
    conflict_resolution_strategy: str = Field(default="prompt", description="Default conflict resolution")
    excluded_patterns: List[str] = Field(default_factory=lambda: ["*.tmp", "*.bak"])
    sync_timeout_seconds: int = Field(default=300, ge=1)


class LibraryConfig(BaseModel):
    """Library configuration settings."""
    base_library_path: Path = Field(default_factory=lambda: Path.home() / ".config" / "ai-configurator" / "library")
    personal_library_path: Path = Field(default_factory=lambda: Path.home() / ".config" / "ai-configurator" / "personal")
    backup_path: Path = Field(default_factory=lambda: Path.home() / ".config" / "ai-configurator" / "backups")
    remote_library_url: Optional[str] = Field(default=None, description="Remote Git repository URL")
    remote_library_path: Optional[str] = Field(default=None, description="Local path for remote library")


class UserPreferences(BaseModel):
    """User-specific preferences and settings."""
    default_editor: Optional[str] = Field(default=None, description="Preferred external editor")
    cli_theme: str = Field(default="default", description="CLI color theme")
    show_progress_bars: bool = Field(default=True)
    confirm_destructive_operations: bool = Field(default=True)
    default_tool_type: ToolType = Field(default=ToolType.Q_CLI)


class BackupInfo(BaseModel):
    """Information about a configuration backup."""
    backup_id: str = Field(..., description="Unique backup identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    backup_type: str = Field(..., description="Type of backup (daily, operation)")
    description: str = Field(default="", description="Backup description")
    file_path: Path = Field(..., description="Path to backup file")
    size_bytes: int = Field(default=0, description="Backup file size")


class Configuration(BaseModel):
    """Core Configuration domain entity."""
    user_preferences: UserPreferences = Field(default_factory=UserPreferences)
    sync_settings: SyncSettings = Field(default_factory=SyncSettings)
    library_config: LibraryConfig = Field(default_factory=LibraryConfig)
    backup_policy: BackupPolicy = Field(default_factory=BackupPolicy)
    tool_settings: Dict[ToolType, Dict[str, Any]] = Field(default_factory=dict)
    backups: List[BackupInfo] = Field(default_factory=list)
    config_version: str = Field(default="4.0.0")
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def add_backup(self, backup: BackupInfo) -> None:
        """Add a new backup to the configuration."""
        self.backups.append(backup)
        self.last_updated = datetime.now()
        
        # Clean up old backups based on policy
        self._cleanup_old_backups()
    
    def get_backup(self, backup_id: str) -> Optional[BackupInfo]:
        """Get backup information by ID."""
        return next((b for b in self.backups if b.backup_id == backup_id), None)
    
    def _cleanup_old_backups(self) -> None:
        """Clean up old backups according to retention policy."""
        now = datetime.now()
        cutoff_date = now.replace(day=now.day - self.backup_policy.backup_retention_days)
        
        # Remove backups older than retention period
        self.backups = [
            backup for backup in self.backups
            if backup.created_at > cutoff_date
        ]
        
        # Limit number of backups by type
        daily_backups = [b for b in self.backups if b.backup_type == "daily"]
        operation_backups = [b for b in self.backups if b.backup_type == "operation"]
        
        # Keep only the most recent backups
        daily_backups.sort(key=lambda x: x.created_at, reverse=True)
        operation_backups.sort(key=lambda x: x.created_at, reverse=True)
        
        kept_backups = (
            daily_backups[:self.backup_policy.max_daily_backups] +
            operation_backups[:self.backup_policy.max_operation_backups]
        )
        
        self.backups = kept_backups
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        # Basic validation
        if self.backup_policy.max_daily_backups < 1:
            return False
        if self.backup_policy.max_operation_backups < 1:
            return False
        if self.sync_settings.sync_timeout_seconds < 1:
            return False
        
        return True
