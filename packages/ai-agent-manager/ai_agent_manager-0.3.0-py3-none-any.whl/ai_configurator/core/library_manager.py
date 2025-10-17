"""
Library Manager for tool-agnostic knowledge library.
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from .file_utils import ensure_directory, copy_file


class LibraryManager:
    """Manages the tool-agnostic knowledge library."""
    
    def __init__(self):
        self.source_library = Path(__file__).parent.parent.parent / "library"
        self.config_dir = Path.home() / ".config" / "ai-configurator"
        self.library_dir = self.config_dir / "library"
    
    def sync_library(self) -> bool:
        """Sync library from source to config directory."""
        try:
            ensure_directory(str(self.config_dir))
            
            # Remove existing library if it exists
            if self.library_dir.exists():
                shutil.rmtree(self.library_dir)
            
            # Copy entire library
            shutil.copytree(self.source_library, self.library_dir)
            
            return True
        except Exception as e:
            print(f"Error syncing library: {e}")
            return False
    
    def ensure_library_synced(self) -> bool:
        """Ensure library is synced, sync if not present."""
        if not self.library_dir.exists():
            return self.sync_library()
        return True
    
    def list_categories(self) -> Dict[str, List[str]]:
        """List all categories and their contents."""
        if not self.ensure_library_synced():
            return {}
        
        categories = {}
        
        for category_dir in self.library_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                files = []
                # Include both .md and .json files
                for file_path in category_dir.rglob("*.md"):
                    relative_path = file_path.relative_to(self.library_dir)
                    files.append(str(relative_path))
                for file_path in category_dir.rglob("*.json"):
                    relative_path = file_path.relative_to(self.library_dir)
                    files.append(str(relative_path))
                categories[category_dir.name] = sorted(files)
        
        return categories
    
    def list_roles(self) -> List[str]:
        """List all available roles."""
        if not self.ensure_library_synced():
            return []
        
        roles_dir = self.library_dir / "roles"
        if not roles_dir.exists():
            return []
        
        roles = []
        for role_dir in roles_dir.iterdir():
            if role_dir.is_dir():
                roles.append(role_dir.name)
        
        return sorted(roles)
    
    def get_role_files(self, role_name: str) -> List[str]:
        """Get all files for a specific role."""
        if not self.ensure_library_synced():
            return []
        
        role_dir = self.library_dir / "roles" / role_name
        if not role_dir.exists():
            return []
        
        files = []
        for file_path in role_dir.glob("*.md"):
            relative_path = file_path.relative_to(self.library_dir)
            files.append(str(relative_path))
        
        return sorted(files)
    
    def get_role_mcp_config(self, role_name: str) -> Optional[Dict]:
        """Get MCP configuration for a specific role."""
        if not self.ensure_library_synced():
            return None
        
        mcp_file = self.library_dir / "roles" / role_name / "mcp.json"
        if not mcp_file.exists():
            return None
        
        try:
            with open(mcp_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading MCP config for {role_name}: {e}")
            return None
    
    def get_common_files(self) -> List[str]:
        """Get all common/organizational files."""
        if not self.ensure_library_synced():
            return []
        
        common_dir = self.library_dir / "common"
        if not common_dir.exists():
            return []
        
        files = []
        for file_path in common_dir.glob("*.md"):
            relative_path = file_path.relative_to(self.library_dir)
            files.append(str(relative_path))
        
        return sorted(files)
    
    def get_file_path(self, relative_path: str) -> Optional[Path]:
        """Get absolute path for a library file."""
        if not self.ensure_library_synced():
            return None
        
        file_path = self.library_dir / relative_path
        if file_path.exists():
            return file_path
        return None
    
    def search_files(self, query: str) -> List[str]:
        """Search for files containing the query."""
        if not self.ensure_library_synced():
            return []
        
        matches = []
        query_lower = query.lower()
        
        for file_path in self.library_dir.rglob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if query_lower in content or query_lower in file_path.name.lower():
                        relative_path = file_path.relative_to(self.library_dir)
                        matches.append(str(relative_path))
            except Exception:
                continue
        
    def get_role_info(self, role_name: str) -> Dict[str, Any]:
        """Get comprehensive information about a role."""
        if not self.ensure_library_synced():
            return {}
        
        role_dir = self.library_dir / "roles" / role_name
        if not role_dir.exists():
            return {}
        
        files = self.get_role_files(role_name)
        mcp_config = self.get_role_mcp_config(role_name)
        
        info = {
            "name": role_name,
            "files": files,
            "file_count": len(files),
            "has_mcp_config": mcp_config is not None
        }
        
        if mcp_config:
            info["mcp_servers"] = list(mcp_config.get("mcpServers", {}).keys())
            info["mcp_server_count"] = len(mcp_config.get("mcpServers", {}))
            info["tools_settings_count"] = len(mcp_config.get("toolsSettings", {}))
            info["allowed_tools_count"] = len(mcp_config.get("allowedTools", []))
        
        return info
    
    def get_library_info(self) -> Dict:
        """Get library information and statistics."""
        if not self.ensure_library_synced():
            return {}
        
        categories = self.list_categories()
        total_files = sum(len(files) for files in categories.values())
        
        return {
            "library_path": str(self.library_dir),
            "source_path": str(self.source_library),
            "categories": categories,
            "total_files": total_files,
            "roles": self.list_roles(),
            "synced": self.library_dir.exists()
        }
