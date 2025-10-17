"""
CLI commands for MCP server registry management.
"""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich.columns import Columns

from ..services.registry_service import RegistryService
from ..services.agent_service import AgentService
from ..models.agent import MCPServerConfig
from ..models.value_objects import ToolType
from ..core.config import ConfigManager


@click.group(name="mcp")
@click.pass_context
def mcp_group(ctx):
    """MCP server registry commands."""
    pass


@mcp_group.command()
@click.option("--category", "-c", help="Filter by category")
@click.option("--limit", "-l", default=20, help="Maximum number of results")
@click.option("--sync", is_flag=True, help="Sync registry before browsing")
@click.pass_context
def browse(ctx, category: Optional[str], limit: int, sync: bool):
    """Browse available MCP servers."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up registry service
        registry_dir = config.library_config.personal_library_path.parent / "registry"
        registry_service = RegistryService(registry_dir, console)
        
        # Sync registry if requested
        if sync:
            registry_service.sync_registry(force=True)
        
        # Get servers
        if category:
            servers = registry_service.search_servers("", category, limit)
            title = f"MCP Servers - {category.title()} Category"
        else:
            servers = registry_service.search_servers("", None, limit)
            title = "Available MCP Servers"
        
        if not servers:
            if category:
                console.print(f"❌ No servers found in category '{category}'")
            else:
                console.print("❌ No servers available. Try running with --sync to update registry.")
            return
        
        # Display servers in a table
        table = Table(title=title)
        table.add_column("Name", style="cyan", width=20)
        table.add_column("Description", style="white", width=40)
        table.add_column("Version", style="yellow", width=10)
        table.add_column("Category", style="green", width=12)
        table.add_column("Rating", style="magenta", width=8)
        
        for server in servers:
            rating_str = f"⭐ {server.rating:.1f}" if server.rating > 0 else "N/A"
            table.add_row(
                server.name,
                server.description[:37] + "..." if len(server.description) > 40 else server.description,
                server.version,
                server.category,
                rating_str
            )
        
        console.print(table)
        
        # Show categories
        categories = registry_service.get_categories()
        if categories:
            console.print(f"\n📂 Available categories: {', '.join(categories)}")
        
        console.print(f"\n💡 Use 'ai-config mcp install <server-name>' to install a server")
        console.print(f"💡 Use 'ai-config mcp search <query>' to search servers")
    
    except Exception as e:
        console.print(f"❌ Error browsing servers: {e}")
        raise click.ClickException(str(e))


@mcp_group.command()
@click.argument("server_name")
@click.option("--force", is_flag=True, help="Force reinstall if already installed")
@click.option("--dry-run", is_flag=True, help="Show what would be installed without installing")
@click.pass_context
def install(ctx, server_name: str, force: bool, dry_run: bool):
    """Install an MCP server."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up registry service
        registry_dir = config.library_config.personal_library_path.parent / "registry"
        registry_service = RegistryService(registry_dir, console)
        
        # Get server details
        server = registry_service.get_server_details(server_name)
        if not server:
            console.print(f"❌ Server '{server_name}' not found in registry")
            console.print("💡 Use 'ai-config mcp browse' to see available servers")
            console.print("💡 Use 'ai-config mcp search <query>' to search for servers")
            return
        
        # Display server information
        info_panel = Panel(
            f"[bold]{server.display_name}[/bold]\n"
            f"Version: {server.version}\n"
            f"Author: {server.author}\n"
            f"Category: {server.category}\n"
            f"Description: {server.description}\n"
            f"Install Type: {server.install_type}\n"
            f"Tools: {', '.join(server.tools[:5])}{'...' if len(server.tools) > 5 else ''}",
            title=f"Server: {server_name}",
            border_style="blue"
        )
        console.print(info_panel)
        
        if dry_run:
            console.print(f"\n🔍 Dry run - would install {server.display_name} v{server.version}")
            console.print(f"📦 Install command: {server.install_command}")
            return
        
        # Check if already installed
        installed_servers = registry_service.get_installed_servers()
        already_installed = any(s.server_name == server_name for s in installed_servers)
        
        if already_installed and not force:
            console.print(f"⚠️  Server '{server_name}' is already installed")
            if not Confirm.ask("Reinstall anyway?"):
                return
            force = True
        
        # Confirm installation
        if not force and not Confirm.ask(f"Install {server.display_name} v{server.version}?"):
            console.print("Installation cancelled")
            return
        
        # Install server
        result = registry_service.install_server(server_name, force)
        
        if result.success:
            console.print(f"✅ Successfully installed {server.display_name}")
            if result.install_path:
                console.print(f"📁 Installed to: {result.install_path}")
        else:
            console.print(f"❌ Installation failed: {result.error_message}")
    
    except Exception as e:
        console.print(f"❌ Error installing server: {e}")
        raise click.ClickException(str(e))


@mcp_group.command()
@click.argument("query")
@click.option("--category", "-c", help="Filter by category")
@click.option("--limit", "-l", default=10, help="Maximum number of results")
@click.pass_context
def search(ctx, query: str, category: Optional[str], limit: int):
    """Search for MCP servers."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up registry service
        registry_dir = config.library_config.personal_library_path.parent / "registry"
        registry_service = RegistryService(registry_dir, console)
        
        # Search servers
        servers = registry_service.search_servers(query, category, limit)
        
        if not servers:
            console.print(f"❌ No servers found matching '{query}'")
            if category:
                console.print(f"   in category '{category}'")
            return
        
        # Display results
        console.print(f"🔍 Found {len(servers)} servers matching '{query}':")
        
        for i, server in enumerate(servers, 1):
            # Highlight matching terms (simplified)
            description = server.description
            if query.lower() in description.lower():
                # Simple highlighting
                description = description.replace(
                    query, f"[bold yellow]{query}[/bold yellow]"
                )
            
            server_panel = Panel(
                f"[bold cyan]{server.display_name}[/bold cyan] ({server.name})\n"
                f"Version: {server.version} | Category: {server.category}\n"
                f"{description}\n"
                f"Tools: {', '.join(server.tools[:3])}{'...' if len(server.tools) > 3 else ''}",
                title=f"{i}. {server.name}",
                border_style="dim"
            )
            console.print(server_panel)
        
        console.print(f"\n💡 Use 'ai-config mcp install <server-name>' to install a server")
    
    except Exception as e:
        console.print(f"❌ Error searching servers: {e}")
        raise click.ClickException(str(e))


@mcp_group.command()
@click.option("--installed", is_flag=True, help="Show only installed servers")
@click.option("--health-check", is_flag=True, help="Check health of installed servers")
@click.pass_context
def status(ctx, installed: bool, health_check: bool):
    """Show MCP server registry status."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up registry service
        registry_dir = config.library_config.personal_library_path.parent / "registry"
        registry_service = RegistryService(registry_dir, console)
        
        if installed:
            # Show installed servers
            installed_servers = registry_service.get_installed_servers()
            
            if not installed_servers:
                console.print("❌ No MCP servers installed")
                return
            
            table = Table(title="Installed MCP Servers")
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="yellow")
            table.add_column("Install Date", style="green")
            table.add_column("Status", style="magenta")
            
            for status in installed_servers:
                # Check health if requested
                if health_check:
                    health = registry_service.check_server_health(status.server_name)
                    status_str = "✅ Healthy" if health.value == "healthy" else "❌ Error"
                else:
                    status_str = "✅ Installed"
                
                install_date = status.install_date.strftime("%Y-%m-%d") if status.install_date else "Unknown"
                
                table.add_row(
                    status.server_name,
                    status.installed_version or "Unknown",
                    install_date,
                    status_str
                )
            
            console.print(table)
        
        else:
            # Show general registry status
            registry = registry_service.load_registry()
            manager = registry_service.load_installation_manager()
            
            status_table = Table(title="MCP Registry Status")
            status_table.add_column("Property", style="cyan")
            status_table.add_column("Value", style="green")
            
            status_table.add_row("Registry Directory", str(registry_dir))
            status_table.add_row("Available Servers", str(len(registry.servers)))
            status_table.add_row("Categories", str(len(registry.categories)))
            status_table.add_row("Installed Servers", str(len(manager.get_installed_servers())))
            status_table.add_row("Last Updated", str(registry.last_updated))
            
            console.print(status_table)
            
            # Show popular servers
            popular = registry_service.get_popular_servers(5)
            if popular:
                console.print("\n🌟 Popular Servers:")
                for server in popular:
                    console.print(f"  • {server.display_name} ({server.name}) - {server.category}")
    
    except Exception as e:
        console.print(f"❌ Error showing status: {e}")
        raise click.ClickException(str(e))


@mcp_group.command()
@click.option("--force", is_flag=True, help="Force sync even if recently updated")
@click.pass_context
def sync(ctx, force: bool):
    """Synchronize MCP server registry."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up registry service
        registry_dir = config.library_config.personal_library_path.parent / "registry"
        registry_service = RegistryService(registry_dir, console)
        
        # Sync registry
        success = registry_service.sync_registry(force)
        
        if success:
            # Show updated stats
            registry = registry_service.load_registry()
            console.print(f"📊 Registry now contains {len(registry.servers)} servers")
            console.print(f"📂 Available categories: {len(registry.categories)}")
        else:
            console.print("❌ Registry sync failed")
    
    except Exception as e:
        console.print(f"❌ Error syncing registry: {e}")
        raise click.ClickException(str(e))


@mcp_group.command(name="create-sample")
@click.pass_context
def create_sample(ctx):
    """Create sample registry for testing."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up registry service
        registry_dir = config.library_config.personal_library_path.parent / "registry"
        registry_service = RegistryService(registry_dir, console)
        
        # Create sample registry
        registry_service.create_sample_registry()
        
        console.print("✅ Sample registry created with test servers")
        console.print("💡 Use 'ai-config mcp browse' to see available servers")
    
    except Exception as e:
        console.print(f"❌ Error creating sample registry: {e}")
        raise click.ClickException(str(e))


@mcp_group.command()
@click.argument("agent_name")
@click.argument("server_name")
@click.argument("command")
@click.option("--args", help="Command arguments (comma-separated)")
@click.option("--env", help="Environment variables (KEY=VALUE,KEY2=VALUE2)")
@click.option("--timeout", type=int, help="Timeout in milliseconds")
def add(agent_name: str, server_name: str, command: str, args: str, env: str, timeout: int):
    """Add MCP server to an agent directly."""
    console = Console()
    
    try:
        # Parse arguments
        server_args = [arg.strip() for arg in args.split(',')] if args else []
        
        # Parse environment variables
        env_vars = {}
        if env:
            for pair in env.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        # Load agent
        config_manager = ConfigManager()
        config = config_manager.load_config()
        agent_service = AgentService(config.library_config.personal_library_path.parent / "agents")
        
        agent = agent_service.load_agent(agent_name, ToolType.Q_CLI)
        if not agent:
            console.print(f"❌ Agent '{agent_name}' not found")
            return
        
        # Create MCP server config
        mcp_config = MCPServerConfig(
            command=command,
            args=server_args,
            env=env_vars,
            timeout=timeout,
            disabled=False
        )
        
        # Add to agent
        agent.configure_mcp_server(server_name, mcp_config)
        
        # Save agent
        if agent_service.update_agent(agent):
            console.print(f"✅ Added MCP server '{server_name}' to agent '{agent_name}'")
            console.print(f"   Command: {command}")
            if server_args:
                console.print(f"   Args: {', '.join(server_args)}")
            if env_vars:
                console.print(f"   Env: {', '.join(f'{k}={v}' for k, v in env_vars.items())}")
            if timeout:
                console.print(f"   Timeout: {timeout}ms")
        else:
            console.print("❌ Failed to update agent")
            
    except Exception as e:
        console.print(f"❌ Error adding MCP server: {e}")


@mcp_group.command()
@click.argument("agent_name")
@click.argument("config_json")
def add_json(agent_name: str, config_json: str):
    """Add MCP server from JSON config snippet."""
    console = Console()
    
    try:
        import json
        
        # Parse JSON config
        config_data = json.loads(config_json)
        
        # Extract server name (should be the key)
        if len(config_data) != 1:
            console.print("❌ JSON should contain exactly one server configuration")
            return
        
        server_name = list(config_data.keys())[0]
        server_config = config_data[server_name]
        
        # Load agent
        config_manager = ConfigManager()
        config = config_manager.load_config()
        agent_service = AgentService(config.library_config.personal_library_path.parent / "agents")
        
        agent = agent_service.load_agent(agent_name, ToolType.Q_CLI)
        if not agent:
            console.print(f"❌ Agent '{agent_name}' not found")
            return
        
        # Create MCP server config
        mcp_config = MCPServerConfig(
            command=server_config.get("command", ""),
            args=server_config.get("args", []),
            env=server_config.get("env", {}),
            timeout=server_config.get("timeout", 120000),  # Default timeout
            disabled=False
        )
        
        # Add to agent
        agent.configure_mcp_server(server_name, mcp_config)
        
        # Save agent
        if agent_service.update_agent(agent):
            console.print(f"✅ Added MCP server '{server_name}' to agent '{agent_name}'")
            console.print(f"   Command: {mcp_config.command}")
            if mcp_config.args:
                console.print(f"   Args: {', '.join(mcp_config.args)}")
            if mcp_config.env:
                console.print(f"   Env: {', '.join(f'{k}={v}' for k, v in mcp_config.env.items())}")
            if mcp_config.timeout:
                console.print(f"   Timeout: {mcp_config.timeout}ms")
        else:
            console.print("❌ Failed to update agent")
            
    except json.JSONDecodeError as e:
        console.print(f"❌ Invalid JSON: {e}")
    except Exception as e:
        console.print(f"❌ Error adding MCP server: {e}")


@mcp_group.command()
@click.argument("agent_name")
def list_servers(agent_name: str):
    """List MCP servers for an agent."""
    console = Console()
    
    try:
        # Load agent
        config_manager = ConfigManager()
        config = config_manager.load_config()
        agent_service = AgentService(config.library_config.personal_library_path.parent / "agents")
        
        agent = agent_service.load_agent(agent_name, ToolType.Q_CLI)
        if not agent:
            console.print(f"❌ Agent '{agent_name}' not found")
            return
        
        if not agent.config.mcp_servers:
            console.print(f"No MCP servers configured for agent '{agent_name}'")
            return
        
        table = Table(title=f"MCP Servers for {agent_name}")
        table.add_column("Name", style="cyan")
        table.add_column("Command", style="white")
        table.add_column("Args", style="green")
        table.add_column("Status", style="yellow")
        
        for name, config in agent.config.mcp_servers.items():
            status = "Disabled" if config.disabled else "Enabled"
            args_str = ", ".join(config.args) if config.args else ""
            
            table.add_row(name, config.command, args_str, status)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error listing MCP servers: {e}")


# Add the mcp group to the main CLI
def register_commands(cli_group):
    """Register MCP registry commands with the main CLI."""
    cli_group.add_command(mcp_group)
