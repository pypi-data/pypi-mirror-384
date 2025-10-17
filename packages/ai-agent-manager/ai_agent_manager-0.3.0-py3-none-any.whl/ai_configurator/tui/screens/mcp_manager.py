"""MCP server management screen."""
import logging
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Button, DataTable, Static
from textual.binding import Binding

from ai_configurator.tui.screens.base import BaseScreen
from ai_configurator.services.registry_service import RegistryService

logger = logging.getLogger(__name__)


class MCPManagerScreen(BaseScreen):
    """MCP server management interface."""
    
    BINDINGS = [
        Binding("a", "add_server", "Add"),
        Binding("e", "edit_server", "Edit"),
        Binding("d", "delete_server", "Delete"),
        Binding("s", "sync_registry", "Sync"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    def __init__(self):
        super().__init__()
        from ai_configurator.tui.config import get_registry_dir
        self.registry_service = RegistryService(get_registry_dir())
        self.registry_dir = get_registry_dir()
        self.selected_server = None
    
    def compose(self) -> ComposeResult:
        """Build screen layout."""
        yield Header()
        yield Container(
            Static("[bold cyan]MCP Server Management[/bold cyan]\n[dim]a=Add e=Edit d=Delete s=Sync r=Refresh[/dim]", id="title"),
            DataTable(id="server_table"),
            id="mcp-container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize table and load data."""
        table = self.query_one(DataTable)
        table.add_columns("Name", "Command", "Status", "Notes")
        table.cursor_type = "row"
        table.focus()
        self.refresh_data()
    
    def refresh_data(self) -> None:
        """Refresh server list."""
        table = self.query_one(DataTable)
        table.clear()
        
        try:
            import json
            from pathlib import Path
            
            # Get all server config files
            servers_dir = self.registry_dir / "servers"
            servers_dir.mkdir(parents=True, exist_ok=True)
            
            servers = []
            for server_file in servers_dir.glob("*.json"):
                try:
                    data = json.loads(server_file.read_text())
                    
                    # Handle different formats
                    if "mcpServers" in data:
                        # Format: {"mcpServers": {"name": {...}}}
                        for name, config in data["mcpServers"].items():
                            servers.append({
                                'name': name,
                                'command': config.get('command', 'Unknown'),
                                'disabled': config.get('disabled', False)
                            })
                    elif "command" in data:
                        # Format: {"command": "...", "args": [...]}
                        servers.append({
                            'name': server_file.stem,
                            'command': data.get('command', 'Unknown'),
                            'disabled': data.get('disabled', False)
                        })
                    else:
                        # Format: {"name": {"command": "...", "args": [...]}}
                        for name, config in data.items():
                            if isinstance(config, dict) and 'command' in config:
                                servers.append({
                                    'name': name,
                                    'command': config.get('command', 'Unknown'),
                                    'disabled': config.get('disabled', False)
                                })
                except Exception as e:
                    logger.error(f"Error reading {server_file}: {e}")
            
            # Also check subdirectories (like filesystem/)
            for subdir in servers_dir.iterdir():
                if subdir.is_dir():
                    config_file = subdir / "config.json"
                    if config_file.exists():
                        try:
                            config = json.loads(config_file.read_text())
                            servers.append({
                                'name': subdir.name,
                                'command': config.get('command', 'Unknown'),
                                'disabled': config.get('disabled', False)
                            })
                        except Exception as e:
                            logger.error(f"Error reading {config_file}: {e}")
            
            # Display servers
            for server in sorted(servers, key=lambda s: s['name']):
                status = "Disabled" if server['disabled'] else "Enabled"
                table.add_row(
                    server['name'],
                    server['command'],
                    status,
                    "-"
                )
            
            # Auto-select first row if available
            if len(servers) > 0:
                self.selected_server = servers[0]['name']
                
        except Exception as e:
            logger.error(f"Error loading servers: {e}", exc_info=True)
            self.show_notification(f"Error loading servers: {e}", "error")
    
    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight (cursor movement)."""
        try:
            table = self.query_one(DataTable)
            if event.cursor_row < table.row_count:
                row = table.get_row_at(event.cursor_row)
                self.selected_server = str(row[0])
        except Exception as e:
            logger.error(f"Error highlighting row: {e}", exc_info=True)
    
    def action_add_server(self) -> None:
        """Add a new MCP server configuration."""
        import json
        import subprocess
        import os
        import shutil
        import tempfile
        
        try:
            # Create an empty temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write("")  # Empty file
                temp_file = f.name
            
            # Open in editor
            editor = os.environ.get('EDITOR')
            if not editor:
                for e in ['kate', 'vim', 'vi', 'nano']:
                    if shutil.which(e):
                        editor = e
                        break
            
            if not editor:
                self.show_notification("No editor found. Set $EDITOR environment variable.", "error")
                return
            
            # Suspend TUI and run editor
            with self.app.suspend():
                if 'kate' in editor:
                    subprocess.run([editor, '--block', temp_file])
                else:
                    subprocess.run([editor, temp_file])
            
            # Read the edited content
            with open(temp_file, 'r') as f:
                content = f.read().strip()
            
            if not content:
                self.show_notification("No content - cancelled", "warning")
                os.unlink(temp_file)
                return
            
            logger.info(f"Read content from temp file: {content[:100]}...")
            
            # Strip trailing comma (common when copying from larger JSON)
            if content.endswith(','):
                content = content[:-1].strip()
                logger.info("Stripped trailing comma")
            
            # Handle case where user pastes just one entry like: "name": {...}
            if content.startswith('"') and ':' in content and not content.startswith('{'):
                logger.info("Wrapping single entry in braces")
                content = '{' + content + '}'
            
            data = json.loads(content)
            logger.info(f"Parsed JSON: {list(data.keys())}")
            
            # Extract server configs
            servers_dir = self.registry_dir / "servers"
            servers_dir.mkdir(parents=True, exist_ok=True)
            
            saved_count = 0
            if "mcpServers" in data:
                # Format: {"mcpServers": {"name": {...}}}
                logger.info("Found mcpServers format")
                for name, config in data["mcpServers"].items():
                    server_file = servers_dir / f"{name}.json"
                    server_file.write_text(json.dumps(config, indent=2))
                    logger.info(f"Saved {name} to {server_file}")
                    saved_count += 1
            elif "command" in data:
                # Direct config - need a name
                logger.warning("Direct config format - needs name wrapper")
                self.show_notification("Please wrap config with server name: {\"name\": {...}}", "warning")
                os.unlink(temp_file)
                return
            else:
                # Format: {"name": {...}}
                logger.info("Found name wrapper format")
                for name, config in data.items():
                    if isinstance(config, dict) and 'command' in config:
                        server_file = servers_dir / f"{name}.json"
                        server_file.write_text(json.dumps(config, indent=2))
                        logger.info(f"Saved {name} to {server_file}")
                        saved_count += 1
            
            # Cleanup temp file
            os.unlink(temp_file)
            
            if saved_count > 0:
                self.show_notification(f"Added {saved_count} server(s)", "information")
                self.refresh_data()
            else:
                self.show_notification("No servers added", "warning")
            
        except json.JSONDecodeError as e:
            self.show_notification(f"Invalid JSON: {e}", "error")
        except Exception as e:
            logger.error(f"Error adding server: {e}", exc_info=True)
            self.show_notification(f"Error: {e}", "error")
    
    def action_edit_server(self) -> None:
        """Edit selected MCP server configuration."""
        import subprocess
        import os
        import shutil
        import json
        
        if not self.selected_server:
            self.show_notification("No server selected", "warning")
            return
        
        try:
            # Find server config file
            server_file = self.registry_dir / "servers" / f"{self.selected_server}.json"
            
            if not server_file.exists():
                self.show_notification(f"Config file not found: {self.selected_server}", "error")
                return
            
            # Open in editor
            editor = os.environ.get('EDITOR')
            if not editor:
                for e in ['kate', 'vim', 'vi', 'nano']:
                    if shutil.which(e):
                        editor = e
                        break
            
            if not editor:
                self.show_notification("No editor found. Set $EDITOR environment variable.", "error")
                return
            
            # Suspend TUI and run editor
            with self.app.suspend():
                subprocess.run([editor, str(server_file)])
            
            # Validate and fix the JSON if needed
            try:
                content = server_file.read_text().strip()
                
                # Handle wrapper format
                if content.startswith('"') and ':' in content and not content.startswith('{'):
                    content = '{' + content + '}'
                    data = json.loads(content)
                    
                    # Extract the actual config and save it properly
                    for name, config in data.items():
                        if isinstance(config, dict) and 'command' in config:
                            server_file.write_text(json.dumps(config, indent=2))
                            break
                else:
                    # Just validate it's valid JSON
                    json.loads(content)
                
                self.show_notification(f"Edited: {self.selected_server}", "information")
                self.refresh_data()
            except json.JSONDecodeError as e:
                self.show_notification(f"Invalid JSON in file: {e}", "error")
                logger.error(f"Invalid JSON after edit: {e}")
            
        except Exception as e:
            logger.error(f"Error editing server: {e}", exc_info=True)
            self.show_notification(f"Error: {e}", "error")
    
    def action_delete_server(self) -> None:
        """Delete selected MCP server configuration."""
        if not self.selected_server:
            self.show_notification("No server selected", "warning")
            return
        
        try:
            server_file = self.registry_dir / "servers" / f"{self.selected_server}.json"
            
            if server_file.exists():
                server_file.unlink()
                self.show_notification(f"Deleted: {self.selected_server}", "information")
                self.selected_server = None
                self.refresh_data()
            else:
                self.show_notification(f"Config file not found: {self.selected_server}", "error")
                
        except Exception as e:
            logger.error(f"Error deleting server: {e}", exc_info=True)
            self.show_notification(f"Error: {e}", "error")
    
    def action_sync_registry(self) -> None:
        """Sync MCP server registry."""
        try:
            self.show_notification("Syncing registry...", "information")
            success = self.registry_service.sync_registry(force=True)
            
            if success:
                self.show_notification("Registry synced successfully", "information")
                self.refresh_data()
            else:
                self.show_notification("Registry sync failed", "error")
                
        except Exception as e:
            logger.error(f"Error syncing registry: {e}", exc_info=True)
            self.show_notification(f"Error: {e}", "error")
