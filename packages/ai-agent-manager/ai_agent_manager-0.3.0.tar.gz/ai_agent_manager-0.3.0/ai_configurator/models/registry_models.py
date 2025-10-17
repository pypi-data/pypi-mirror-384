"""
MCP server registry models for server discovery and installation.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field, HttpUrl

from .value_objects import HealthStatus


class MCPServerMetadata(BaseModel):
    """Detailed metadata for an MCP server."""
    name: str = Field(..., description="Server name")
    display_name: str = Field(..., description="Human-readable display name")
    description: str = Field(..., description="Server description")
    version: str = Field(..., description="Server version")
    author: str = Field(default="", description="Server author")
    homepage: Optional[HttpUrl] = Field(default=None, description="Homepage URL")
    repository: Optional[HttpUrl] = Field(default=None, description="Repository URL")
    
    # Installation info
    install_command: str = Field(..., description="Installation command")
    install_type: str = Field(..., description="Installation type: npm, pip, binary, etc.")
    requirements: List[str] = Field(default_factory=list, description="System requirements")
    
    # Categorization
    category: str = Field(default="general", description="Server category")
    tags: List[str] = Field(default_factory=list, description="Server tags")
    
    # Capabilities
    tools: List[str] = Field(default_factory=list, description="Available tools")
    resources: List[str] = Field(default_factory=list, description="Available resources")
    
    # Compatibility
    platforms: List[str] = Field(default_factory=lambda: ["linux", "macos", "windows"], description="Supported platforms")
    min_version: Optional[str] = Field(default=None, description="Minimum MCP version required")
    
    # Registry metadata
    registry_updated: datetime = Field(default_factory=datetime.now, description="Last registry update")
    download_count: int = Field(default=0, description="Download count")
    rating: float = Field(default=0.0, ge=0.0, le=5.0, description="User rating")
    
    def is_compatible(self, platform: str) -> bool:
        """Check if server is compatible with platform."""
        return platform.lower() in [p.lower() for p in self.platforms]
    
    def matches_search(self, query: str) -> bool:
        """Check if server matches search query."""
        query_lower = query.lower()
        return (
            query_lower in self.name.lower() or
            query_lower in self.display_name.lower() or
            query_lower in self.description.lower() or
            any(query_lower in tag.lower() for tag in self.tags) or
            query_lower in self.category.lower()
        )


class InstallationStatus(BaseModel):
    """Status of an MCP server installation."""
    server_name: str = Field(..., description="Server name")
    installed: bool = Field(default=False, description="Whether server is installed")
    install_path: Optional[Path] = Field(default=None, description="Installation path")
    installed_version: Optional[str] = Field(default=None, description="Installed version")
    install_date: Optional[datetime] = Field(default=None, description="Installation date")
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN, description="Health status")
    last_check: Optional[datetime] = Field(default=None, description="Last health check")
    
    def needs_update(self, available_version: str) -> bool:
        """Check if server needs updating."""
        if not self.installed or not self.installed_version:
            return True
        
        # Simple version comparison (could be enhanced)
        try:
            installed_parts = [int(x) for x in self.installed_version.split('.')]
            available_parts = [int(x) for x in available_version.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(installed_parts), len(available_parts))
            installed_parts.extend([0] * (max_len - len(installed_parts)))
            available_parts.extend([0] * (max_len - len(available_parts)))
            
            return available_parts > installed_parts
        except ValueError:
            # If version parsing fails, assume update needed
            return True


class InstallationResult(BaseModel):
    """Result of an installation operation."""
    server_name: str = Field(..., description="Server name")
    success: bool = Field(..., description="Installation success")
    install_path: Optional[Path] = Field(default=None, description="Installation path")
    version: Optional[str] = Field(default=None, description="Installed version")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    install_time: datetime = Field(default_factory=datetime.now, description="Installation time")
    
    def to_status(self) -> InstallationStatus:
        """Convert to InstallationStatus."""
        return InstallationStatus(
            server_name=self.server_name,
            installed=self.success,
            install_path=self.install_path,
            installed_version=self.version,
            install_date=self.install_time if self.success else None,
            health_status=HealthStatus.HEALTHY if self.success else HealthStatus.ERROR
        )


class MCPServerRegistry(BaseModel):
    """Registry of available MCP servers."""
    servers: Dict[str, MCPServerMetadata] = Field(default_factory=dict, description="Available servers")
    categories: Dict[str, List[str]] = Field(default_factory=dict, description="Servers by category")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last registry update")
    registry_version: str = Field(default="1.0.0", description="Registry format version")
    
    def add_server(self, server: MCPServerMetadata) -> None:
        """Add a server to the registry."""
        self.servers[server.name] = server
        
        # Update categories
        if server.category not in self.categories:
            self.categories[server.category] = []
        
        if server.name not in self.categories[server.category]:
            self.categories[server.category].append(server.name)
        
        self.last_updated = datetime.now()
    
    def get_server(self, name: str) -> Optional[MCPServerMetadata]:
        """Get server by name."""
        return self.servers.get(name)
    
    def search_servers(self, query: str, category: Optional[str] = None) -> List[MCPServerMetadata]:
        """Search servers by query and optional category."""
        results = []
        
        for server in self.servers.values():
            # Filter by category if specified
            if category and server.category != category:
                continue
            
            # Check if matches search query
            if not query or server.matches_search(query):
                results.append(server)
        
        # Sort by relevance (rating, then download count)
        results.sort(key=lambda s: (s.rating, s.download_count), reverse=True)
        return results
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return sorted(self.categories.keys())
    
    def get_servers_by_category(self, category: str) -> List[MCPServerMetadata]:
        """Get all servers in a category."""
        server_names = self.categories.get(category, [])
        return [self.servers[name] for name in server_names if name in self.servers]
    
    def get_popular_servers(self, limit: int = 10) -> List[MCPServerMetadata]:
        """Get most popular servers."""
        servers = list(self.servers.values())
        servers.sort(key=lambda s: (s.download_count, s.rating), reverse=True)
        return servers[:limit]


class InstallationManager(BaseModel):
    """Manages MCP server installations."""
    install_directory: Path = Field(..., description="Base installation directory")
    installations: Dict[str, InstallationStatus] = Field(default_factory=dict, description="Installation statuses")
    
    def get_installation_status(self, server_name: str) -> InstallationStatus:
        """Get installation status for a server."""
        return self.installations.get(
            server_name, 
            InstallationStatus(server_name=server_name)
        )
    
    def update_installation_status(self, status: InstallationStatus) -> None:
        """Update installation status for a server."""
        self.installations[status.server_name] = status
    
    def get_installed_servers(self) -> List[InstallationStatus]:
        """Get all installed servers."""
        return [status for status in self.installations.values() if status.installed]
    
    def get_outdated_servers(self, registry: MCPServerRegistry) -> List[tuple[InstallationStatus, MCPServerMetadata]]:
        """Get servers that need updates."""
        outdated = []
        
        for status in self.installations.values():
            if not status.installed:
                continue
            
            server_meta = registry.get_server(status.server_name)
            if server_meta and status.needs_update(server_meta.version):
                outdated.append((status, server_meta))
        
        return outdated
    
    def cleanup_failed_installations(self) -> int:
        """Remove failed installation records."""
        failed_servers = [
            name for name, status in self.installations.items()
            if not status.installed and status.health_status == HealthStatus.ERROR
        ]
        
        for server_name in failed_servers:
            del self.installations[server_name]
        
        return len(failed_servers)
