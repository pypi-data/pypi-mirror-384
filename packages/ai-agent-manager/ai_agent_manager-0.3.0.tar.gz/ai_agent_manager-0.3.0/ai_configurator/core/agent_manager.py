"""
Agent Manager for creating and managing tool-specific agents.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from .file_utils import ensure_directory
from .library_manager import LibraryManager


class AgentConfig:
    """Agent configuration model."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.resources = []
        self.tools = ["*"]
        self.allowed_tools = ["fs_read"]
        self.mcp_servers = {}
        self.tools_settings = {}
    
    def add_resource(self, file_path: str):
        """Add a resource file to the agent."""
        self.resources.append(f"file://{file_path}")
    
    def add_mcp_server(self, name: str, config: Dict[str, Any]):
        """Add an MCP server configuration."""
        self.mcp_servers[name] = config
    
    def merge_mcp_config(self, mcp_config: Dict[str, Any]):
        """Merge MCP configuration from role."""
        if "mcpServers" in mcp_config:
            # Replace existing MCP servers completely to ensure updates are applied
            self.mcp_servers = mcp_config["mcpServers"].copy()
        
        if "toolsSettings" in mcp_config:
            self.tools_settings.update(mcp_config["toolsSettings"])
        
        if "allowedTools" in mcp_config:
            # Replace allowed tools completely to ensure updates are applied
            self.allowed_tools = mcp_config["allowedTools"].copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        config = {
            "$schema": "https://raw.githubusercontent.com/aws/amazon-q-developer-cli/refs/heads/main/schemas/agent-v1.json",
            "name": self.name,
            "description": self.description,
            "resources": self.resources,
            "tools": self.tools,
            "allowedTools": self.allowed_tools
        }
        
        if self.mcp_servers:
            config["mcpServers"] = self.mcp_servers
        
        if self.tools_settings:
            config["toolsSettings"] = self.tools_settings
        
        return config


class AgentManager:
    """Manages tool-specific agents."""
    
    def __init__(self, tool: str = "q-cli"):
        self.tool = tool
        self.library_manager = LibraryManager()
        self.config_dir = Path.home() / ".config" / "ai-configurator"
        self.tool_dir = self.config_dir / tool
        self.agents_dir = self.tool_dir / "agents"
        self.mcp_dir = self.tool_dir / "mcp-servers"
        
        # Ensure directories exist
        ensure_directory(str(self.agents_dir))
        ensure_directory(str(self.mcp_dir))
    
    def create_agent(self, name: str, rules: List[str], description: str = "") -> bool:
        """Create a new agent with specified rules."""
        try:
            # Ensure library is synced
            if not self.library_manager.ensure_library_synced():
                return False
            
            # Create agent config
            agent = AgentConfig(name, description)
            
            # Add resources
            for rule in rules:
                file_path = self.library_manager.get_file_path(rule)
                if file_path:
                    agent.add_resource(str(file_path))
                else:
                    print(f"Warning: Rule file not found: {rule}")
            
            # Load role-specific MCP configurations
            self._add_role_mcp_configs(agent, rules)
            
            # Load and add MCP servers from backup if available
            self._add_default_mcp_servers(agent)
            
            # Save agent configuration
            agent_file = self.agents_dir / f"{name}.json"
            with open(agent_file, 'w', encoding='utf-8') as f:
                json.dump(agent.to_dict(), f, indent=2)
            
            # Create Amazon Q CLI agent if tool is q-cli
            if self.tool == "q-cli":
                self._create_q_cli_agent(name, agent.to_dict())
            
            return True
        except Exception as e:
            print(f"Error creating agent: {e}")
            return False
    
    def update_agent(self, name: str) -> bool:
        """Update an existing agent (interactive)."""
        agent_file = self.agents_dir / f"{name}.json"
        if not agent_file.exists():
            print(f"Agent '{name}' not found")
            return False
        
        try:
            # Load existing config
            with open(agent_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Interactive menu
            while True:
                print(f"\n{name} Agent Configuration:")
                print("1. Add/Remove Knowledge Files")
                print("2. Configure MCP Servers")
                print("3. Modify Agent Settings")
                print("4. Save and Exit")
                print("5. Cancel")
                
                choice = input("Select option (1-5): ").strip()
                
                if choice == "1":
                    self._manage_knowledge_files(config)
                elif choice == "2":
                    self._manage_mcp_servers(config)
                elif choice == "3":
                    self._manage_agent_settings(config)
                elif choice == "4":
                    # Save updated config
                    with open(agent_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)
                    
                    # Update Amazon Q CLI agent if tool is q-cli
                    if self.tool == "q-cli":
                        self._create_q_cli_agent(name, config)
                    
                    print(f"Agent '{name}' updated successfully")
                    return True
                elif choice == "5":
                    print("Update cancelled")
                    return False
                else:
                    print("Invalid option, please try again")
        
        except Exception as e:
            print(f"Error updating agent: {e}")
            return False

    def update_all_agents(self) -> bool:
        """Update all existing agents with latest library configurations."""
        try:
            agents = self.list_agents()
            if not agents:
                print("No agents found to update")
                return True
            
            success_count = 0
            for agent_name in agents:
                print(f"Updating agent: {agent_name}")
                if self._update_agent_config(agent_name):
                    success_count += 1
                    print(f"  ✅ {agent_name} updated")
                else:
                    print(f"  ❌ {agent_name} failed")
            
            print(f"Updated {success_count}/{len(agents)} agents")
            return success_count == len(agents)
        except Exception as e:
            print(f"Error updating agents: {e}")
            return False
    
    def _update_agent_config(self, name: str) -> bool:
        """Update a single agent configuration without interactive prompts."""
        agent_file = self.agents_dir / f"{name}.json"
        if not agent_file.exists():
            return False
        
        try:
            # Load existing config
            with open(agent_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Recreate agent with current library configurations
            resources = config.get("resources", [])
            rules = []
            
            # Extract rule paths from resources
            for resource in resources:
                if resource.startswith("file://"):
                    file_path = resource.replace("file://", "")
                    # Convert absolute path back to relative library path
                    if str(self.library_manager.library_dir) in file_path:
                        relative_path = Path(file_path).relative_to(self.library_manager.library_dir)
                        rules.append(str(relative_path))
            
            # Create new agent config
            agent = AgentConfig(name, config.get("description", ""))
            
            # Add resources
            for rule in rules:
                file_path = self.library_manager.get_file_path(rule)
                if file_path:
                    agent.add_resource(str(file_path))
            
            # Load role-specific MCP configurations
            self._add_role_mcp_configs(agent, rules)
            
            # Save updated config
            with open(agent_file, 'w', encoding='utf-8') as f:
                json.dump(agent.to_dict(), f, indent=2)
            
            # Update Amazon Q CLI agent if tool is q-cli
            if self.tool == "q-cli":
                self._create_q_cli_agent(name, agent.to_dict())
            
            return True
        except Exception as e:
            print(f"Error updating {name}: {e}")
            return False
        """Update an existing agent (interactive)."""
        agent_file = self.agents_dir / f"{name}.json"
        if not agent_file.exists():
            print(f"Agent '{name}' not found")
            return False
        
        try:
            # Load existing config
            with open(agent_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Interactive menu
            while True:
                print(f"\n{name} Agent Configuration:")
                print("1. Add/Remove Knowledge Files")
                print("2. Configure MCP Servers")
                print("3. Modify Agent Settings")
                print("4. Save and Exit")
                print("5. Cancel")
                
                choice = input("Select option (1-5): ").strip()
                
                if choice == "1":
                    self._manage_knowledge_files(config)
                elif choice == "2":
                    self._manage_mcp_servers(config)
                elif choice == "3":
                    self._manage_agent_settings(config)
                elif choice == "4":
                    # Save updated config
                    with open(agent_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)
                    
                    # Update Amazon Q CLI agent if tool is q-cli
                    if self.tool == "q-cli":
                        self._create_q_cli_agent(name, config)
                    
                    print(f"Agent '{name}' updated successfully")
                    return True
                elif choice == "5":
                    print("Update cancelled")
                    return False
                else:
                    print("Invalid option, please try again")
        
        except Exception as e:
            print(f"Error updating agent: {e}")
            return False
    
    def list_agents(self) -> List[str]:
        """List all agents for this tool."""
        if not self.agents_dir.exists():
            return []
        
        agents = []
        for agent_file in self.agents_dir.glob("*.json"):
            agents.append(agent_file.stem)
        
        return sorted(agents)
    
    def remove_agent(self, name: str) -> bool:
        """Remove an agent."""
        try:
            agent_file = self.agents_dir / f"{name}.json"
            if agent_file.exists():
                agent_file.unlink()
            
            # Remove Amazon Q CLI agent if tool is q-cli
            if self.tool == "q-cli":
                q_cli_agent_file = Path.home() / ".aws" / "amazonq" / "cli-agents" / f"{name}.json"
                if q_cli_agent_file.exists():
                    q_cli_agent_file.unlink()
            
            return True
        except Exception as e:
            print(f"Error removing agent: {e}")
            return False
    
    def get_agent_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent information."""
        agent_file = self.agents_dir / f"{name}.json"
        if not agent_file.exists():
            return None
        
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _add_role_mcp_configs(self, agent: AgentConfig, rules: List[str]):
        """Add MCP configurations from registry (updated approach)."""
        # Load MCP servers from registry directory instead of role files
        registry_dir = self.config_dir / "registry" / "servers"
        if registry_dir.exists():
            for server_file in registry_dir.glob("*.json"):
                try:
                    with open(server_file, 'r', encoding='utf-8') as f:
                        server_config = json.load(f)
                    server_name = server_file.stem
                    agent.add_mcp_server(server_name, server_config)
                except Exception as e:
                    print(f"Warning: Could not load MCP server {server_file.stem}: {e}")
        
        # Fallback: Load from role-specific files for backward compatibility
        for rule in rules:
            if rule.startswith("roles/") and "/" in rule:
                role_name = rule.split("/")[1]
                mcp_config = self.library_manager.get_role_mcp_config(role_name)
                if mcp_config:
                    agent.merge_mcp_config(mcp_config)
                    print(f"Loaded MCP config for role: {role_name}")
    
    def _add_default_mcp_servers(self, agent: AgentConfig):
        """Add default MCP servers from backup."""
        backup_mcp_file = Path(__file__).parent.parent.parent / "backup" / "mcp-servers" / "core.json"
        if backup_mcp_file.exists():
            try:
                with open(backup_mcp_file, 'r', encoding='utf-8') as f:
                    mcp_data = json.load(f)
                    if "mcpServers" in mcp_data:
                        for name, config in mcp_data["mcpServers"].items():
                            agent.add_mcp_server(name, config)
            except Exception as e:
                print(f"Warning: Could not load MCP servers: {e}")
    
    def _create_q_cli_agent(self, name: str, config: Dict[str, Any]):
        """Create Amazon Q CLI agent file."""
        q_cli_agents_dir = Path.home() / ".aws" / "amazonq" / "cli-agents"
        ensure_directory(str(q_cli_agents_dir))
        
        agent_file = q_cli_agents_dir / f"{name}.json"
        with open(agent_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def _manage_knowledge_files(self, config: Dict[str, Any]):
        """Interactive knowledge file management."""
        print("\nCurrent knowledge files:")
        resources = config.get("resources", [])
        for i, resource in enumerate(resources, 1):
            # Extract filename from file:// path
            filename = resource.replace("file://", "").split("/")[-1]
            print(f"  {i}. {filename}")
        
        print("\nAvailable categories:")
        categories = self.library_manager.list_categories()
        for category, files in categories.items():
            print(f"  {category}: {len(files)} files")
        
        print("\n1. Add knowledge file")
        print("2. Remove knowledge file")
        print("3. Back to main menu")
        
        choice = input("Select option (1-3): ").strip()
        
        if choice == "1":
            self._add_knowledge_file(config)
        elif choice == "2":
            self._remove_knowledge_file(config)
    
    def _add_knowledge_file(self, config: Dict[str, Any]):
        """Add a knowledge file to the agent."""
        categories = self.library_manager.list_categories()
        
        print("\nSelect category:")
        category_list = list(categories.keys())
        for i, category in enumerate(category_list, 1):
            print(f"  {i}. {category}")
        
        try:
            cat_choice = int(input("Category number: ")) - 1
            if 0 <= cat_choice < len(category_list):
                category = category_list[cat_choice]
                files = categories[category]
                
                print(f"\nFiles in {category}:")
                for i, file_path in enumerate(files, 1):
                    print(f"  {i}. {file_path}")
                
                file_choice = int(input("File number: ")) - 1
                if 0 <= file_choice < len(files):
                    selected_file = files[file_choice]
                    full_path = self.library_manager.get_file_path(selected_file)
                    if full_path:
                        resource_path = f"file://{full_path}"
                        if resource_path not in config.get("resources", []):
                            config.setdefault("resources", []).append(resource_path)
                            print(f"Added: {selected_file}")
                        else:
                            print("File already added")
        except (ValueError, IndexError):
            print("Invalid selection")
    
    def _remove_knowledge_file(self, config: Dict[str, Any]):
        """Remove a knowledge file from the agent."""
        resources = config.get("resources", [])
        if not resources:
            print("No knowledge files to remove")
            return
        
        print("\nSelect file to remove:")
        for i, resource in enumerate(resources, 1):
            filename = resource.replace("file://", "").split("/")[-1]
            print(f"  {i}. {filename}")
        
        try:
            choice = int(input("File number: ")) - 1
            if 0 <= choice < len(resources):
                removed = resources.pop(choice)
                filename = removed.replace("file://", "").split("/")[-1]
                print(f"Removed: {filename}")
        except (ValueError, IndexError):
            print("Invalid selection")
    
    def _manage_mcp_servers(self, config: Dict[str, Any]):
        """Interactive MCP server management."""
        mcp_servers = config.get("mcpServers", {})
        
        print("\nCurrent MCP servers:")
        for name, server_config in mcp_servers.items():
            print(f"  {name}: {server_config.get('command', 'N/A')}")
        
        print("\n1. Add MCP server")
        print("2. Remove MCP server")
        print("3. Back to main menu")
        
        choice = input("Select option (1-3): ").strip()
        
        if choice == "1":
            self._add_mcp_server(config)
        elif choice == "2":
            self._remove_mcp_server(config)
    
    def _add_mcp_server(self, config: Dict[str, Any]):
        """Add an MCP server."""
        name = input("MCP server name: ").strip()
        command = input("Command: ").strip()
        args_input = input("Arguments (comma-separated, optional): ").strip()
        
        args = [arg.strip() for arg in args_input.split(",")] if args_input else []
        
        server_config = {
            "command": command,
            "args": args,
            "env": {},
            "disabled": False,
            "autoApprove": []
        }
        
        config.setdefault("mcpServers", {})[name] = server_config
        print(f"Added MCP server: {name}")
    
    def _remove_mcp_server(self, config: Dict[str, Any]):
        """Remove an MCP server."""
        mcp_servers = config.get("mcpServers", {})
        if not mcp_servers:
            print("No MCP servers to remove")
            return
        
        print("\nSelect MCP server to remove:")
        server_list = list(mcp_servers.keys())
        for i, name in enumerate(server_list, 1):
            print(f"  {i}. {name}")
        
        try:
            choice = int(input("Server number: ")) - 1
            if 0 <= choice < len(server_list):
                server_name = server_list[choice]
                del mcp_servers[server_name]
                print(f"Removed MCP server: {server_name}")
        except (ValueError, IndexError):
            print("Invalid selection")
    
    def _manage_agent_settings(self, config: Dict[str, Any]):
        """Interactive agent settings management."""
        print(f"\nCurrent settings:")
        print(f"  Name: {config.get('name', 'N/A')}")
        print(f"  Description: {config.get('description', 'N/A')}")
        print(f"  Tools: {config.get('tools', [])}")
        print(f"  Allowed Tools: {config.get('allowedTools', [])}")
        
        print("\n1. Update description")
        print("2. Back to main menu")
        
        choice = input("Select option (1-2): ").strip()
        
        if choice == "1":
            new_description = input("New description: ").strip()
            config["description"] = new_description
            print("Description updated")
