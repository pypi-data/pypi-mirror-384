"""
CLI commands for local file management.
"""

from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from ..models.file_models import FilePattern, FileWatchConfig, FileWatcher
from ..models.value_objects import ToolType
from ..services.file_service import FileService
from ..services.agent_service import AgentService
from ..core.config import ConfigManager


@click.group(name="files")
@click.pass_context
def files_group(ctx):
    """Local file management commands."""
    pass


@files_group.command(name="scan-files")
@click.argument("agent_name")
@click.option("--pattern", "-p", multiple=True, help="Patterns to scan")
@click.option("--base-path", "-b", type=click.Path(exists=True, path_type=Path),
              help="Base path for patterns")
@click.option("--add-found", is_flag=True, help="Automatically add found files to agent")
@click.pass_context
def scan_files(ctx, agent_name: str, pattern: tuple, base_path: Optional[Path], add_found: bool):
    """Scan for files matching patterns and optionally add them to agent."""
    console = Console()
    
    try:
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up services
        agent_service = AgentService(config.library_config.personal_library_path.parent / "agents")
        file_service = FileService(console)
        
        # Load agent - try to find any agent with this name
        agent = None
        for tool_type in ToolType:
            agent = agent_service.load_agent(agent_name, tool_type)
            if agent:
                break
        
        if not agent:
            console.print(f"❌ Agent '{agent_name}' not found")
            return
        
        # Use default patterns if none specified
        if not pattern:
            pattern = ("**/*.md", "**/*.txt", "**/*.py")
            console.print(f"🔍 Using default patterns: {pattern}")
        
        if not base_path:
            base_path = Path.cwd()
        
        # Create file patterns
        patterns = []
        for p in pattern:
            file_pattern = FilePattern(
                pattern=p,
                base_path=base_path,
                recursive=True
            )
            patterns.append(file_pattern)
        
        # Discover files
        console.print(f"🔍 Scanning for files in: {base_path}")
        result = file_service.discover_files(patterns)
        
        if result.errors:
            console.print("⚠️  Errors during scan:")
            for error in result.errors:
                console.print(f"  • {error}")
        
        if not result.discovered_files:
            console.print("❌ No files found matching the patterns")
            return
        
        # Display results by pattern
        for pattern_str, count in result.matched_patterns.items():
            console.print(f"📁 Pattern '{pattern_str}': {count} files")
        
        # Show sample files
        console.print(f"\n📄 Sample files (showing first 10 of {result.total_files}):")
        for i, file_path in enumerate(result.discovered_files[:10]):
            console.print(f"  {i+1}. {file_path}")
        
        if result.total_files > 10:
            console.print(f"  ... and {result.total_files - 10} more files")
        
        if result.excluded_files:
            console.print(f"\n🚫 Excluded {len(result.excluded_files)} files")
        
        if add_found:
            if Confirm.ask(f"\nAdd all {result.total_files} files to agent '{agent_name}'?"):
                # Add files to agent
                added_count = 0
                for file_path in result.discovered_files:
                    from ..models.value_objects import ResourcePath, LibrarySource
                    resource_path = ResourcePath(
                        path=str(file_path),
                        source=LibrarySource.LOCAL
                    )
                    agent.add_resource(resource_path)
                    added_count += 1
                
                # Save agent
                if agent_service.update_agent(agent):
                    console.print(f"✅ Added {added_count} files to agent '{agent_name}'")
                else:
                    console.print("❌ Failed to save agent")
            else:
                console.print("Operation cancelled")
    
    except Exception as e:
        console.print(f"❌ Error scanning files: {e}")
        raise click.ClickException(str(e))


# Add the files group to the main CLI
def register_commands(cli_group):
    """Register file commands with the main CLI."""
    cli_group.add_command(files_group)
