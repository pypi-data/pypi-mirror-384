"""
Pydantic models for AI Configurator domain entities.
"""

from .agent import Agent, AgentConfig, AgentSettings
from .configuration import Configuration, UserPreferences, SyncSettings, LibraryConfig, BackupPolicy, BackupInfo
from .library import Library, LibraryMetadata, LibraryFile, ConflictInfo
from .mcp_server import MCPServer, MCPServerConfig
from .sync_models import LibrarySync, ConflictReport, SyncHistory, SyncOperation, FileDiff
from .file_models import FilePattern, LocalResource, FileWatcher, FileWatchConfig, FileDiscoveryResult
from .registry_models import MCPServerRegistry, MCPServerMetadata, InstallationManager, InstallationStatus, InstallationResult
from .wizard_models import Wizard, WizardStep, Template, TemplateLibrary, WizardResult
from .value_objects import ResourcePath, ToolType, LibrarySource, ConflictType, Resolution, SyncStatus, HealthStatus

__all__ = [
    # Core entities
    "Agent",
    "Configuration", 
    "Library",
    "MCPServer",
    # Configuration models
    "AgentConfig",
    "AgentSettings",
    "UserPreferences",
    "SyncSettings",
    "LibraryConfig", 
    "BackupInfo",
    "LibraryMetadata",
    "LibraryFile",
    "ConflictInfo",
    "MCPServerConfig",
    # Sync models
    "LibrarySync",
    "ConflictReport", 
    "SyncHistory",
    "SyncOperation",
    "FileDiff",
    # File models
    "FilePattern",
    "LocalResource",
    "FileWatcher", 
    "FileWatchConfig",
    "FileDiscoveryResult",
    # Registry models
    "MCPServerRegistry",
    "MCPServerMetadata",
    "InstallationManager",
    "InstallationStatus", 
    "InstallationResult",
    # Wizard models
    "Wizard",
    "WizardStep",
    "Template",
    "TemplateLibrary",
    "WizardResult",
    # Value objects
    "ResourcePath",
    "ToolType",
    "LibrarySource",
    "ConflictType",
    "Resolution",
    "SyncStatus",
    "HealthStatus",
]
