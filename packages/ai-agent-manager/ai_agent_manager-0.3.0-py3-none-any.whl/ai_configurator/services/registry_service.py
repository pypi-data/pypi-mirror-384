"""
MCP server registry service for discovery and installation.
"""

import json
import subprocess
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..models.registry_models import (
    MCPServerRegistry, MCPServerMetadata, InstallationManager, 
    InstallationStatus, InstallationResult
)
from ..models.value_objects import HealthStatus


class RegistryService:
    """Service for MCP server registry operations."""
    
    def __init__(self, registry_dir: Path, console: Optional[Console] = None):
        self.registry_dir = registry_dir
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.console = console or Console()
        
        self.registry_file = registry_dir / "registry.json"
        self.installations_file = registry_dir / "installations.json"
        
        # Default registry URLs (could be configurable)
        self.registry_urls = [
            "https://raw.githubusercontent.com/modelcontextprotocol/servers/main/registry.json",
            # Add more registry sources as they become available
        ]
        
        # Ensure default MCP servers exist
        self._ensure_default_servers()
    
    def _ensure_default_servers(self) -> None:
        """Copy default MCP server configs if they don't exist."""
        import ai_configurator
        import shutil
        
        source_servers = Path(ai_configurator.__file__).parent.parent / "library" / "mcp-servers"
        servers_dir = self.registry_dir / "servers"
        servers_dir.mkdir(parents=True, exist_ok=True)
        
        if source_servers.exists():
            for server_file in source_servers.glob("*.json"):
                dest_file = servers_dir / server_file.name
                if not dest_file.exists():
                    shutil.copy2(server_file, dest_file)
    
    def load_registry(self) -> MCPServerRegistry:
        """Load registry from local file or create empty one."""
        if self.registry_file.exists():
            try:
                data = json.loads(self.registry_file.read_text())
                return MCPServerRegistry(**data)
            except Exception as e:
                self.console.print(f"⚠️  Failed to load registry: {e}")
        
        return MCPServerRegistry()
    
    def save_registry(self, registry: MCPServerRegistry) -> bool:
        """Save registry to local file."""
        try:
            data = registry.dict()
            self.registry_file.write_text(json.dumps(data, indent=2, default=str))
            return True
        except Exception as e:
            self.console.print(f"❌ Failed to save registry: {e}")
            return False
    
    def load_installation_manager(self) -> InstallationManager:
        """Load installation manager from file."""
        install_dir = self.registry_dir / "servers"
        install_dir.mkdir(exist_ok=True)
        
        manager = InstallationManager(install_directory=install_dir)
        
        if self.installations_file.exists():
            try:
                data = json.loads(self.installations_file.read_text())
                manager.installations = {
                    name: InstallationStatus(**status_data)
                    for name, status_data in data.get("installations", {}).items()
                }
            except Exception as e:
                self.console.print(f"⚠️  Failed to load installations: {e}")
        
        return manager
    
    def save_installation_manager(self, manager: InstallationManager) -> bool:
        """Save installation manager to file."""
        try:
            data = {
                "install_directory": str(manager.install_directory),
                "installations": {
                    name: status.dict()
                    for name, status in manager.installations.items()
                }
            }
            self.installations_file.write_text(json.dumps(data, indent=2, default=str))
            return True
        except Exception as e:
            self.console.print(f"❌ Failed to save installations: {e}")
            return False
    
    def sync_registry(self, force: bool = False) -> bool:
        """Synchronize registry with remote sources."""
        registry = self.load_registry()
        
        # Check if sync is needed
        if not force and registry.last_updated:
            hours_since_update = (datetime.now() - registry.last_updated).total_seconds() / 3600
            if hours_since_update < 24:  # Don't sync more than once per day
                return True
        
        self.console.print("🔄 Synchronizing MCP server registry...")
        
        updated = False
        for url in self.registry_urls:
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console
                ) as progress:
                    task = progress.add_task(f"Fetching from {url}...", total=None)
                    
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    remote_data = response.json()
                    
                    # Parse remote registry data
                    if "servers" in remote_data:
                        for server_data in remote_data["servers"]:
                            try:
                                server = MCPServerMetadata(**server_data)
                                registry.add_server(server)
                                updated = True
                            except Exception as e:
                                self.console.print(f"⚠️  Invalid server data: {e}")
                    
                    progress.update(task, completed=True)
                    
            except Exception as e:
                self.console.print(f"⚠️  Failed to sync from {url}: {e}")
        
        if updated:
            if self.save_registry(registry):
                self.console.print("✅ Registry synchronized successfully")
                return True
            else:
                self.console.print("❌ Failed to save updated registry")
                return False
        else:
            self.console.print("ℹ️  Registry is up to date")
            return True
    
    def search_servers(self, query: str = "", category: Optional[str] = None, 
                      limit: int = 20) -> List[MCPServerMetadata]:
        """Search for MCP servers."""
        registry = self.load_registry()
        results = registry.search_servers(query, category)
        return results[:limit]
    
    def get_server_details(self, server_name: str) -> Optional[MCPServerMetadata]:
        """Get detailed information about a server."""
        registry = self.load_registry()
        return registry.get_server(server_name)
    
    def get_categories(self) -> List[str]:
        """Get all available server categories."""
        registry = self.load_registry()
        return registry.get_categories()
    
    def install_server(self, server_name: str, force: bool = False) -> InstallationResult:
        """Install an MCP server."""
        registry = self.load_registry()
        manager = self.load_installation_manager()
        
        server = registry.get_server(server_name)
        if not server:
            return InstallationResult(
                server_name=server_name,
                success=False,
                error_message=f"Server '{server_name}' not found in registry"
            )
        
        # Check if already installed
        status = manager.get_installation_status(server_name)
        if status.installed and not force:
            return InstallationResult(
                server_name=server_name,
                success=True,
                install_path=status.install_path,
                version=status.installed_version,
                error_message="Server already installed (use --force to reinstall)"
            )
        
        # Check platform compatibility
        current_platform = platform.system().lower()
        if not server.is_compatible(current_platform):
            return InstallationResult(
                server_name=server_name,
                success=False,
                error_message=f"Server not compatible with {current_platform}"
            )
        
        self.console.print(f"📦 Installing {server.display_name} ({server.version})...")
        
        try:
            # Create server-specific install directory
            server_dir = manager.install_directory / server_name
            server_dir.mkdir(parents=True, exist_ok=True)
            
            # Execute installation command
            install_cmd = server.install_command.format(
                install_dir=str(server_dir),
                server_name=server_name
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Installing...", total=None)
                
                result = subprocess.run(
                    install_cmd,
                    shell=True,
                    cwd=server_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                progress.update(task, completed=True)
            
            if result.returncode == 0:
                # Installation successful
                install_result = InstallationResult(
                    server_name=server_name,
                    success=True,
                    install_path=server_dir,
                    version=server.version
                )
                
                # Update installation status
                status = install_result.to_status()
                manager.update_installation_status(status)
                self.save_installation_manager(manager)
                
                self.console.print(f"✅ Successfully installed {server.display_name}")
                return install_result
            
            else:
                # Installation failed
                error_msg = result.stderr or result.stdout or "Installation failed"
                return InstallationResult(
                    server_name=server_name,
                    success=False,
                    error_message=error_msg
                )
        
        except subprocess.TimeoutExpired:
            return InstallationResult(
                server_name=server_name,
                success=False,
                error_message="Installation timed out"
            )
        except Exception as e:
            return InstallationResult(
                server_name=server_name,
                success=False,
                error_message=str(e)
            )
    
    def uninstall_server(self, server_name: str) -> bool:
        """Uninstall an MCP server."""
        manager = self.load_installation_manager()
        status = manager.get_installation_status(server_name)
        
        if not status.installed:
            self.console.print(f"⚠️  Server '{server_name}' is not installed")
            return False
        
        try:
            # Remove installation directory
            if status.install_path and status.install_path.exists():
                import shutil
                shutil.rmtree(status.install_path)
            
            # Remove from installation manager
            if server_name in manager.installations:
                del manager.installations[server_name]
            
            self.save_installation_manager(manager)
            self.console.print(f"✅ Successfully uninstalled {server_name}")
            return True
            
        except Exception as e:
            self.console.print(f"❌ Failed to uninstall {server_name}: {e}")
            return False
    
    def get_installed_servers(self) -> List[InstallationStatus]:
        """Get list of installed servers."""
        manager = self.load_installation_manager()
        return manager.get_installed_servers()
    
    def check_server_health(self, server_name: str) -> HealthStatus:
        """Check health of an installed server."""
        manager = self.load_installation_manager()
        status = manager.get_installation_status(server_name)
        
        if not status.installed or not status.install_path:
            return HealthStatus.ERROR
        
        try:
            # Basic health check - verify installation directory exists
            if not status.install_path.exists():
                return HealthStatus.ERROR
            
            # Could add more sophisticated health checks here
            # For now, assume healthy if installed and directory exists
            return HealthStatus.HEALTHY
            
        except Exception:
            return HealthStatus.ERROR
    
    def get_popular_servers(self, limit: int = 10) -> List[MCPServerMetadata]:
        """Get most popular servers."""
        registry = self.load_registry()
        return registry.get_popular_servers(limit)
    
    def create_sample_registry(self) -> None:
        """Create a sample registry for testing."""
        registry = MCPServerRegistry()
        
        # Add some sample servers
        sample_servers = [
            MCPServerMetadata(
                name="filesystem",
                display_name="File System Server",
                description="Provides file system access and operations",
                version="1.0.0",
                author="MCP Team",
                install_command="npm install -g @modelcontextprotocol/server-filesystem",
                install_type="npm",
                category="system",
                tags=["filesystem", "files", "system"],
                tools=["read_file", "write_file", "list_directory"],
                platforms=["linux", "macos", "windows"]
            ),
            MCPServerMetadata(
                name="git",
                display_name="Git Server",
                description="Git repository operations and version control",
                version="1.2.0",
                author="MCP Team",
                install_command="npm install -g @modelcontextprotocol/server-git",
                install_type="npm",
                category="development",
                tags=["git", "version-control", "development"],
                tools=["git_status", "git_commit", "git_log"],
                platforms=["linux", "macos", "windows"]
            ),
            MCPServerMetadata(
                name="database",
                display_name="Database Server",
                description="Database operations and SQL queries",
                version="2.1.0",
                author="Community",
                install_command="pip install mcp-server-database",
                install_type="pip",
                category="data",
                tags=["database", "sql", "data"],
                tools=["execute_query", "describe_table", "list_tables"],
                platforms=["linux", "macos", "windows"]
            )
        ]
        
        for server in sample_servers:
            registry.add_server(server)
        
        self.save_registry(registry)
        self.console.print("✅ Sample registry created")
