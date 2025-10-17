"""
CLI commands for interactive wizards.
"""

import click
from rich.console import Console

from ..services.wizard_service import WizardService
from ..services.agent_service import AgentService
from ..services.registry_service import RegistryService
from ..services.library_service import LibraryService
from ..core.config import ConfigManager


@click.group(name="wizard")
@click.pass_context
def wizard_group(ctx):
    """Interactive setup wizards."""
    pass


@wizard_group.command(name="create-agent")
@click.pass_context
def create_agent_wizard(ctx):
    """Interactive agent creation wizard."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up services
        agent_service = AgentService(config.library_config.personal_library_path.parent / "agents")
        library_service = LibraryService(
            config.library_config.base_library_path,
            config.library_config.personal_library_path
        )
        wizard_service = WizardService(library_service, console)
        
        # Run wizard
        agent_name = wizard_service.run_agent_creation_wizard(agent_service)
        
        if agent_name:
            console.print(f"\n🎉 Agent '{agent_name}' is ready to use!")
            console.print(f"💡 Use 'ai-config export-agent {agent_name} --save' to export to Q CLI")
        else:
            console.print("\n❌ Agent creation was cancelled or failed")
    
    except Exception as e:
        console.print(f"❌ Error in agent creation wizard: {e}")
        raise click.ClickException(str(e))


@wizard_group.command(name="add-mcp-json")
@click.argument("agent_name", required=False)
@click.pass_context
def add_mcp_json_wizard(ctx, agent_name: str):
    """Add MCP servers from JSON snippet. If no agent specified, adds to registry only."""
    console = Console()
    
    try:
        if agent_name:
            console.print(f"🧙 [bold]Add MCP Servers to {agent_name}[/bold]")
        else:
            console.print(f"🧙 [bold]Add MCP Servers to Registry[/bold]")
            
        console.print("Paste your JSON snippet from fastmcp.me or other registries")
        console.print("Supports both formats:")
        console.print('• {"mcpServers": {...}}')
        console.print('• {"server-name": {...}}')
        console.print()
        
        from rich.prompt import Prompt, Confirm
        
        # Ask how to input JSON
        console.print("Choose JSON input method:")
        console.print("1. External editor (safest)")
        console.print("2. Multiline input (type JSON, then empty line)")
        console.print("3. Single line (wrap in quotes)")
        
        method = Prompt.ask("Input method", choices=["1", "2", "3"], default="2")
        
        if method == "1":
            json_snippet = _get_json_from_editor()
            if not json_snippet:
                console.print("❌ No JSON provided from editor")
                return
        elif method == "2":
            console.print("Enter JSON (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if line.strip() == "" and lines:
                    break
                lines.append(line)
            json_snippet = "\n".join(lines)
        else:
            console.print("💡 Wrap JSON in single quotes to avoid shell interpretation")
            json_snippet = Prompt.ask("Paste JSON snippet")
        
        if not json_snippet.strip():
            console.print("❌ No JSON provided")
            return
        
        import json
        
        # Parse JSON with fragment handling
        try:
            # First try direct parsing
            config_data = json.loads(json_snippet)
        except json.JSONDecodeError as e:
            # Try to fix common issues
            fixed_json = json_snippet.strip()
            
            # Remove trailing comma if present
            if fixed_json.endswith(','):
                fixed_json = fixed_json[:-1]
            
            # If it looks like a single server object, wrap it
            if fixed_json.startswith('"') and '": {' in fixed_json and not fixed_json.startswith('{'):
                fixed_json = '{' + fixed_json + '}'
            
            try:
                config_data = json.loads(fixed_json)
                console.print("✅ Fixed JSON formatting")
            except json.JSONDecodeError:
                console.print(f"❌ Invalid JSON: {e}")
                console.print("💡 Make sure JSON is complete and properly formatted")
                console.print("💡 Example: {\"server-name\": {\"command\": \"npx\", \"args\": [\"package\"]}}")
                return
        
        # Handle fastmcp.me format with mcpServers wrapper
        if "mcpServers" in config_data:
            servers_config = config_data["mcpServers"]
            console.print("✅ Detected fastmcp.me format")
        else:
            servers_config = config_data
            console.print("✅ Detected direct server config format")
        
        if not servers_config:
            console.print("❌ No server configurations found")
            return
        
        # Load services
        from ..core.config import ConfigManager
        from ..services.registry_service import RegistryService
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        registry_dir = config.library_config.personal_library_path.parent / "registry"
        registry_service = RegistryService(registry_dir, console)
        
        agent = None
        agent_service = None
        
        # Load agent if specified
        if agent_name:
            from ..services.agent_service import AgentService
            from ..models.value_objects import ToolType
            
            agent_service = AgentService(config.library_config.personal_library_path.parent / "agents")
            agent = agent_service.load_agent(agent_name, ToolType.Q_CLI)
            if not agent:
                console.print(f"❌ Agent '{agent_name}' not found")
                return
        
        # Process each server
        added_servers = []
        for server_name, server_config in servers_config.items():
            try:
                from ..models.agent import MCPServerConfig
                
                # Create MCP server config with Q CLI defaults
                mcp_config = MCPServerConfig(
                    command=server_config.get("command", ""),
                    args=server_config.get("args", []),
                    env=server_config.get("env", {}),
                    timeout=server_config.get("timeout", 120000),
                    disabled=False
                )
                
                # Add to agent if specified
                if agent:
                    agent.configure_mcp_server(server_name, mcp_config)
                
                added_servers.append((server_name, mcp_config))
                
            except Exception as e:
                console.print(f"⚠️  Failed to add server '{server_name}': {e}")
        
        # Save agent if specified
        if agent and agent_service and added_servers:
            if agent_service.update_agent(agent):
                console.print(f"\n✅ Added {len(added_servers)} MCP server(s) to agent '{agent_name}':")
            else:
                console.print("❌ Failed to update agent")
                return
        elif added_servers and not agent_name:
            console.print(f"\n✅ Processed {len(added_servers)} MCP server(s):")
            console.print("💡 Note: Registry addition not yet implemented")
            console.print("💡 Use with agent name to add directly: ai-config wizard add-mcp-json <agent>")
        
        # Show added servers
        for server_name, mcp_config in added_servers:
            console.print(f"   • {server_name}: {mcp_config.command}")
            if mcp_config.args:
                console.print(f"     Args: {', '.join(mcp_config.args)}")
            if mcp_config.env:
                console.print(f"     Env: {', '.join(f'{k}={v}' for k, v in mcp_config.env.items())}")
            
    except Exception as e:
        console.print(f"❌ Error in MCP JSON wizard: {e}")


def _get_json_from_editor():
    """Open external editor for JSON input."""
    import tempfile
    import subprocess
    import os
    
    # Create temporary file with helpful template
    template = '''{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["package@latest"],
      "env": {
        "LOG_LEVEL": "INFO"
      },
      "timeout": 120000
    }
  }
}

// OR direct format:
// {
//   "server-name": {
//     "command": "uvx", 
//     "args": ["package@latest"]
//   }
// }

// Replace this template with your JSON from fastmcp.me or other registries
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(template)
        temp_file = f.name
    
    try:
        # Try different editors
        editors = ['code', 'vim', 'nano', 'gedit']
        
        for editor in editors:
            try:
                if editor == 'code':
                    # VS Code - wait for file to be saved and closed
                    subprocess.run([editor, '--wait', temp_file], check=True)
                else:
                    subprocess.run([editor, temp_file], check=True)
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        else:
            print("❌ No suitable editor found (tried: code, vim, nano, gedit)")
            return None
        
        # Read the edited content
        with open(temp_file, 'r') as f:
            content = f.read().strip()
        
        # Remove comments and template text
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('//') or 'Replace this template' in line:
                continue
            lines.append(line)
        
        cleaned_content = '\n'.join(lines).strip()
        return cleaned_content
        
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file)
        except:
            pass


@wizard_group.command(name="setup-mcp")
@click.argument("agent_name")
@click.pass_context
def setup_mcp_wizard(ctx, agent_name: str):
    """Interactive MCP server setup wizard."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up services
        registry_dir = config.library_config.personal_library_path.parent / "registry"
        registry_service = RegistryService(registry_dir, console)
        library_service = LibraryService(
            config.library_config.base_library_path,
            config.library_config.personal_library_path
        )
        wizard_service = WizardService(library_service, console)
        
        # Run wizard
        success = wizard_service.run_mcp_setup_wizard(agent_name, registry_service)
        
        if success:
            console.print(f"\n✅ MCP setup completed for agent '{agent_name}'")
        else:
            console.print(f"\n❌ MCP setup was cancelled or failed")
    
    except Exception as e:
        console.print(f"❌ Error in MCP setup wizard: {e}")
        raise click.ClickException(str(e))


@wizard_group.command(name="quick-start")
@click.pass_context
def quick_start_wizard(ctx):
    """Complete quick start wizard for new users."""
    console = Console()
    
    try:
        console.print("🚀 Welcome to AI Configurator Quick Start!")
        console.print("This wizard will help you set up your first AI agent.\n")
        
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up services
        agent_service = AgentService(config.library_config.personal_library_path.parent / "agents")
        registry_dir = config.library_config.personal_library_path.parent / "registry"
        registry_service = RegistryService(registry_dir, console)
        library_service = LibraryService(
            config.library_config.base_library_path,
            config.library_config.personal_library_path
        )
        wizard_service = WizardService(library_service, console)
        
        # Step 1: Create agent
        console.print("📋 Step 1: Create your first agent")
        agent_name = wizard_service.run_agent_creation_wizard(agent_service)
        
        if not agent_name:
            console.print("❌ Quick start cancelled")
            return
        
        # Step 2: Set up MCP servers (optional)
        from rich.prompt import Confirm
        if Confirm.ask("\n🔧 Would you like to set up MCP servers for enhanced capabilities?", default=True):
            console.print("\n📋 Step 2: Configure MCP servers")
            
            # Create sample registry if it doesn't exist
            registry = registry_service.load_registry()
            if not registry.servers:
                console.print("📦 Creating sample MCP server registry...")
                registry_service.create_sample_registry()
            
            wizard_service.run_mcp_setup_wizard(agent_name, registry_service)
        
        # Step 3: Export to Q CLI
        if Confirm.ask(f"\n📤 Export agent '{agent_name}' to Q CLI for immediate use?", default=True):
            # This would integrate with the existing export functionality
            console.print(f"💡 Run: ai-config export-agent {agent_name} --save")
        
        console.print(f"\n🎉 Quick start completed!")
        console.print(f"✅ Agent '{agent_name}' is ready to use")
        console.print(f"💡 Use 'ai-config status' to see your configuration")
        console.print(f"💡 Use 'ai-config manage-agent {agent_name}' for advanced configuration")
    
    except Exception as e:
        console.print(f"❌ Error in quick start wizard: {e}")
        raise click.ClickException(str(e))


# Add the wizard group to the main CLI
def register_commands(cli_group):
    """Register wizard commands with the main CLI."""
    cli_group.add_command(wizard_group)
