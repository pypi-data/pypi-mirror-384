"""Agent editing screen with dual-pane interface."""
import logging
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Label, Input, SelectionList
from textual.widgets.selection_list import Selection
from textual.binding import Binding

from ai_configurator.tui.screens.base import BaseScreen
from ai_configurator.services.agent_service import AgentService
from ai_configurator.services.library_service import LibraryService
from ai_configurator.services.registry_service import RegistryService
from ai_configurator.models import Agent, ToolType, ResourcePath, AgentConfig

logger = logging.getLogger(__name__)


class AgentEditScreen(BaseScreen):
    """Agent editing interface with dual-pane layout."""
    
    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("space", "toggle_checkbox", "Toggle"),
        Binding("t", "toggle_trust", "Trust/Untrust"),
        Binding("a", "add_pattern", "Add Pattern"),
        Binding("d", "remove_pattern", "Delete Pattern"),
        Binding("e", "edit_pattern", "Edit Pattern"),
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, agent: Agent, agent_service: AgentService):
        super().__init__()
        self.agent = agent
        self.agent_service = agent_service
        
        # Get available items
        from ai_configurator.tui.config import get_library_paths, get_registry_dir
        base_path, personal_path = get_library_paths()
        self.library_service = LibraryService(base_path, personal_path)
        self.registry_service = RegistryService(get_registry_dir())
        self.library_root_path = personal_path.parent
        
        # Load available files - scan entire library folder
        self.available_files = {}
        for md_file in self.library_root_path.rglob("*.md"):
            if md_file.is_file():
                relative_path = str(md_file.relative_to(self.library_root_path))
                self.available_files[relative_path] = relative_path
        
        # Load MCP servers
        import json
        servers_dir = get_registry_dir() / "servers"
        self.available_servers = {}
        
        if servers_dir.exists():
            for server_file in servers_dir.glob("*.json"):
                try:
                    data = json.loads(server_file.read_text())
                    if "mcpServers" in data:
                        for name in data["mcpServers"].keys():
                            self.available_servers[name] = data["mcpServers"][name]
                    elif "command" in data:
                        self.available_servers[server_file.stem] = data
                    else:
                        for name, config in data.items():
                            if isinstance(config, dict) and 'command' in config:
                                self.available_servers[name] = config
                except Exception as e:
                    logger.error(f"Error loading {server_file}: {e}")
        
        # Pre-select items already in agent
        # Match both old format (templates/file.md) and new format (base/templates/file.md)
        self.selected_files = set()
        for resource in agent.config.resources:
            # Try exact match first
            if resource.path in self.available_files:
                self.selected_files.add(resource.path)
            else:
                # Try matching by filename in any folder
                from pathlib import Path
                resource_name = Path(resource.path).name
                for available_path in self.available_files.keys():
                    if Path(available_path).name == resource_name:
                        self.selected_files.add(available_path)
                        break
        
        self.selected_servers = set(name for name in agent.config.mcp_servers.keys() if name in self.available_servers)
        
        # Track trusted servers (those with autoApprove tools)
        self.trusted_servers = set()
        for name, server_config in agent.config.mcp_servers.items():
            if hasattr(server_config, 'auto_approve') and server_config.auto_approve:
                self.trusted_servers.add(name)
        
        # Context patterns management
        self.context_patterns = list(agent.config.context_patterns)
    
    def compose(self) -> ComposeResult:
        """Build layout."""
        from textual.containers import VerticalScroll
        
        yield Header()
        yield Container(
            Static(f"[bold cyan]Edit Agent: {self.agent.name}[/bold cyan]\n[dim]Click to select/trust | T=Trust Ctrl+S=Save A=Add D=Delete E=Edit Esc=Cancel[/dim]", id="title"),
            
            # Context patterns section
            Vertical(
                Label("[bold]Context File Patterns[/bold]"),
                VerticalScroll(
                    DataTable(id="patterns_table", classes="patterns-table"),
                    classes="scroll-container",
                    can_focus=False
                ),
                classes="patterns-section"
            ),
            
            # Library files section
            Vertical(
                Label("[bold]Library Files[/bold]"),
                VerticalScroll(
                    DataTable(id="available_files", classes="files-table"),
                    classes="scroll-container",
                    can_focus=False
                ),
                classes="files-section"
            ),
            
            # MCP servers section
            Vertical(
                Label("[bold]MCP Servers[/bold]"),
                VerticalScroll(
                    DataTable(id="available_servers", classes="servers-table"),
                    classes="scroll-container",
                    can_focus=False
                ),
                classes="servers-section"
            ),
            
            id="edit-container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize widgets."""
        # Setup patterns table
        patterns_table = self.query_one("#patterns_table", DataTable)
        patterns_table.add_column("Pattern")
        patterns_table.cursor_type = "row"
        patterns_table.can_focus = True
        
        # Setup files table with selection column
        files_table = self.query_one("#available_files", DataTable)
        files_table.add_column("Selected", width=10)
        files_table.add_column("File", width=60)
        files_table.cursor_type = "cell"
        files_table.zebra_stripes = True
        files_table.show_cursor = True
        files_table.can_focus = True
        
        # Setup servers table with selection and trust columns
        servers_table = self.query_one("#available_servers", DataTable)
        servers_table.add_column("Selected", width=10)
        servers_table.add_column("Trusted", width=10)
        servers_table.add_column("Server", width=40)
        servers_table.cursor_type = "cell"
        servers_table.zebra_stripes = True
        servers_table.show_cursor = True
        servers_table.can_focus = True
        
        self.refresh_all_tables()
        patterns_table.focus()
    
    def refresh_all_tables(self) -> None:
        """Refresh all widgets."""
        from pathlib import Path
        from collections import defaultdict
        
        # Patterns table
        patterns_table = self.query_one("#patterns_table", DataTable)
        patterns_table.clear()
        for pattern in self.context_patterns:
            patterns_table.add_row(pattern)
        
        # Available files - populate DataTable with selection column
        files_table = self.query_one("#available_files", DataTable)
        files_table.clear()
        
        # Group by folder
        files_by_folder = defaultdict(list)
        for path in self.available_files.keys():
            folder = str(Path(path).parent)
            files_by_folder[folder].append(path)
        
        # Add files grouped by folder
        for folder in sorted(files_by_folder.keys()):
            # Add folder header
            files_table.add_row("", f"[bold cyan]{folder}/[/bold cyan]")
            
            # Add files in this folder
            for path in sorted(files_by_folder[folder]):
                selected_mark = "[green]✓[/green]" if path in self.selected_files else "[dim]○[/dim]"
                filename = Path(path).name
                files_table.add_row(selected_mark, f"  {filename}")
        
        # Available servers - populate DataTable with selection and trust columns
        servers_table = self.query_one("#available_servers", DataTable)
        servers_table.clear()
        for name in sorted(self.available_servers.keys()):
            selected_mark = "[green]✓[/green]" if name in self.selected_servers else "[dim]○[/dim]"
            trusted_mark = "[yellow]★[/yellow]" if name in self.trusted_servers else "[dim]○[/dim]"
            servers_table.add_row(selected_mark, trusted_mark, name)
    
    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle cell selection - toggle based on which column is clicked."""
        from pathlib import Path
        
        try:
            if event.data_table.id == "available_files":
                # If clicking on file name column, move cursor to checkbox column
                if event.coordinate.column != 0:
                    event.data_table.move_cursor(
                        row=event.coordinate.row,
                        column=0
                    )
                    return
                
                row = event.data_table.get_row_at(event.coordinate.row)
                file_display = str(row[1]).strip()
                
                # Skip folder headers
                if file_display.startswith("[bold"):
                    return
                
                # Extract filename and find full path
                filename = file_display.strip()
                
                # Find current folder by looking backwards
                current_folder = None
                for i in range(event.coordinate.row - 1, -1, -1):
                    check_row = event.data_table.get_row_at(i)
                    check_text = str(check_row[1]).strip()
                    if check_text.startswith("[bold cyan]"):
                        current_folder = check_text.replace("[bold cyan]", "").replace("[/bold cyan]", "").rstrip("/")
                        break
                
                if current_folder:
                    full_path = f"{current_folder}/{filename}"
                    
                    # Toggle selection
                    if full_path in self.selected_files:
                        self.selected_files.discard(full_path)
                    else:
                        self.selected_files.add(full_path)
                    
                    # Refresh and restore cursor to checkbox column
                    cursor_row = event.coordinate.row
                    self.refresh_all_tables()
                    event.data_table.focus()
                    if event.data_table.row_count > 0:
                        event.data_table.move_cursor(
                            row=min(cursor_row, event.data_table.row_count - 1),
                            column=0
                        )
            
            elif event.data_table.id == "available_servers":
                row = event.data_table.get_row_at(event.coordinate.row)
                server_name = str(row[2])  # Server name is now in column 2
                
                # Column 0 = Selected, Column 1 = Trusted, Column 2 = Name
                if event.coordinate.column == 0:
                    # Toggle selection
                    if server_name in self.selected_servers:
                        self.selected_servers.discard(server_name)
                    else:
                        self.selected_servers.add(server_name)
                    
                    # Refresh and restore cursor
                    cursor_row = event.coordinate.row
                    self.refresh_all_tables()
                    event.data_table.focus()
                    if event.data_table.row_count > 0:
                        event.data_table.move_cursor(
                            row=min(cursor_row, event.data_table.row_count - 1),
                            column=0
                        )
                    
                elif event.coordinate.column == 1:
                    # Toggle trust
                    if server_name in self.trusted_servers:
                        self.trusted_servers.discard(server_name)
                    else:
                        self.trusted_servers.add(server_name)
                    
                    # Refresh and restore cursor
                    cursor_row = event.coordinate.row
                    self.refresh_all_tables()
                    event.data_table.focus()
                    if event.data_table.row_count > 0:
                        event.data_table.move_cursor(
                            row=min(cursor_row, event.data_table.row_count - 1),
                            column=1
                        )
                else:
                    # Column 2 (server name) - move cursor to checkbox column
                    event.data_table.move_cursor(
                        row=event.coordinate.row,
                        column=0
                    )
                        
        except Exception as e:
            logger.error(f"Error handling cell click: {e}", exc_info=True)
    
    def action_toggle_checkbox(self) -> None:
        """Toggle checkbox at current cursor position (Space key)."""
        from pathlib import Path
        
        focused = self.app.focused
        if focused is None:
            return
        
        try:
            if focused.id == "available_files":
                files_table = self.query_one("#available_files", DataTable)
                cursor_row = files_table.cursor_row
                cursor_col = files_table.cursor_column
                
                # Only toggle if on checkbox column (0)
                if cursor_col != 0:
                    return
                
                row = files_table.get_row_at(cursor_row)
                file_display = str(row[1]).strip()
                
                # Skip folder headers
                if file_display.startswith("[bold"):
                    return
                
                # Find full path
                filename = file_display.strip()
                current_folder = None
                for i in range(cursor_row - 1, -1, -1):
                    check_row = files_table.get_row_at(i)
                    check_text = str(check_row[1]).strip()
                    if check_text.startswith("[bold cyan]"):
                        current_folder = check_text.replace("[bold cyan]", "").replace("[/bold cyan]", "").rstrip("/")
                        break
                
                if current_folder:
                    full_path = f"{current_folder}/{filename}"
                    
                    # Toggle selection
                    if full_path in self.selected_files:
                        self.selected_files.discard(full_path)
                    else:
                        self.selected_files.add(full_path)
                    
                    # Refresh and restore cursor
                    self.refresh_all_tables()
                    files_table.focus()
                    if files_table.row_count > 0:
                        files_table.move_cursor(row=min(cursor_row, files_table.row_count - 1), column=0)
            
            elif focused.id == "available_servers":
                servers_table = self.query_one("#available_servers", DataTable)
                cursor_row = servers_table.cursor_row
                cursor_col = servers_table.cursor_column
                
                row = servers_table.get_row_at(cursor_row)
                server_name = str(row[2])
                
                # Column 0 = Selected, Column 1 = Trusted
                if cursor_col == 0:
                    # Toggle selection
                    if server_name in self.selected_servers:
                        self.selected_servers.discard(server_name)
                    else:
                        self.selected_servers.add(server_name)
                    
                    # Refresh and restore cursor
                    self.refresh_all_tables()
                    servers_table.focus()
                    if servers_table.row_count > 0:
                        servers_table.move_cursor(row=min(cursor_row, servers_table.row_count - 1), column=0)
                
                elif cursor_col == 1:
                    # Toggle trust
                    if server_name in self.trusted_servers:
                        self.trusted_servers.discard(server_name)
                    else:
                        self.trusted_servers.add(server_name)
                    
                    # Refresh and restore cursor
                    self.refresh_all_tables()
                    servers_table.focus()
                    if servers_table.row_count > 0:
                        servers_table.move_cursor(row=min(cursor_row, servers_table.row_count - 1), column=1)
                        
        except Exception as e:
            logger.error(f"Error toggling checkbox: {e}", exc_info=True)
    
    def action_toggle_trust(self) -> None:
        """Toggle trust status of selected MCP server."""
        focused = self.app.focused
        if focused is None or focused.id != "available_servers":
            return
        
        try:
            servers_table = self.query_one("#available_servers", DataTable)
            if servers_table.cursor_row < servers_table.row_count:
                cursor_row = servers_table.cursor_row
                row = servers_table.get_row_at(cursor_row)
                server_name = str(row[1])  # Server name is in second column
                
                # Toggle trust
                if server_name in self.trusted_servers:
                    self.trusted_servers.discard(server_name)
                else:
                    self.trusted_servers.add(server_name)
                
                # Refresh to update trust indicator
                self.refresh_all_tables()
                
                # Restore cursor and focus
                servers_table.focus()
                if servers_table.row_count > 0:
                    servers_table.move_cursor(row=min(cursor_row, servers_table.row_count - 1))
                
        except Exception as e:
            logger.error(f"Error toggling trust: {e}", exc_info=True)
    
    def action_add_pattern(self) -> None:
        """Add a new context pattern."""
        from textual.widgets import Input
        from textual.screen import ModalScreen
        from textual.containers import Vertical
        
        class PatternInputScreen(ModalScreen):
            """Simple pattern input screen."""
            def compose(self):
                yield Vertical(
                    Static("[bold]Add Context Pattern[/bold]\nEnter file pattern (e.g., .amazonq/rules/**/*.md):"),
                    Input(placeholder="**/*.md", id="pattern_input"),
                    id="input_dialog"
                )
            
            def on_input_submitted(self, event: Input.Submitted):
                self.dismiss(event.value)
        
        def handle_pattern(pattern: str) -> None:
            if pattern and pattern.strip():
                self.context_patterns.append(pattern.strip())
                self.refresh_all_tables()
        
        self.app.push_screen(PatternInputScreen(), handle_pattern)
    
    def action_remove_pattern(self) -> None:
        """Remove selected pattern."""
        patterns_table = self.query_one("#patterns_table", DataTable)
        if patterns_table.cursor_row < len(self.context_patterns):
            del self.context_patterns[patterns_table.cursor_row]
            self.refresh_all_tables()
    
    def action_edit_pattern(self) -> None:
        """Edit selected pattern."""
        patterns_table = self.query_one("#patterns_table", DataTable)
        if patterns_table.cursor_row < len(self.context_patterns):
            current_pattern = self.context_patterns[patterns_table.cursor_row]
            
            from textual.widgets import Input
            from textual.screen import ModalScreen
            from textual.containers import Vertical
            
            class PatternEditScreen(ModalScreen):
                """Pattern edit screen."""
                def compose(self):
                    yield Vertical(
                        Static("[bold]Edit Context Pattern[/bold]"),
                        Input(placeholder="**/*.md", id="pattern_input", value=current_pattern),
                        id="input_dialog"
                    )
                
                def on_input_submitted(self, event: Input.Submitted):
                    self.dismiss(event.value)
            
            def handle_edit(pattern: str) -> None:
                if pattern and pattern.strip():
                    self.context_patterns[patterns_table.cursor_row] = pattern.strip()
                    self.refresh_all_tables()
            
            self.app.push_screen(PatternEditScreen(), handle_edit)
    
    def action_save(self) -> None:
        """Save agent changes."""
        try:
            # Use the managed context patterns list
            context_patterns = self.context_patterns
            
            # Build new resource list
            new_resources = []
            for path in self.selected_files:
                if path in self.available_files:
                    # Determine source from path (base/ or personal/)
                    from ai_configurator.models import LibrarySource
                    source = LibrarySource.BASE if path.startswith("base/") else LibrarySource.PERSONAL
                    
                    new_resources.append(ResourcePath(
                        path=path,
                        source=source
                    ))
            
            # Build new MCP servers dict and collect trusted tools
            new_mcp_servers = {}
            trusted_tools = []
            
            for server_name in self.selected_servers:
                if server_name in self.available_servers:
                    # Use the actual server config from registry
                    server_config = self.available_servers[server_name]
                    from ai_configurator.models.mcp_server import MCPServerConfig
                    
                    # Set auto_approve based on trust status
                    auto_approve = ["*"] if server_name in self.trusted_servers else []
                    
                    # Add to trusted tools if trusted
                    if server_name in self.trusted_servers:
                        trusted_tools.append(f"@{server_name}/*")
                    
                    new_mcp_servers[server_name] = MCPServerConfig(
                        command=server_config.get("command", server_name),
                        args=server_config.get("args", []),
                        env=server_config.get("env"),
                        timeout=server_config.get("timeout", 120000),
                        disabled=server_config.get("disabled", False),
                        auto_approve=auto_approve
                    )
                elif server_name in self.agent.config.mcp_servers:
                    # Keep existing config
                    new_mcp_servers[server_name] = self.agent.config.mcp_servers[server_name]
            
            # Update allowed tools to include trusted MCP server tools
            current_allowed_tools = list(self.agent.config.settings.allowed_tools)
            # Remove existing MCP tool entries
            current_allowed_tools = [tool for tool in current_allowed_tools if not tool.startswith("@")]
            # Add trusted MCP tools
            current_allowed_tools.extend(trusted_tools)
            
            # Create new config
            new_config = AgentConfig(
                name=self.agent.config.name,
                description=self.agent.config.description,
                prompt=self.agent.config.prompt,
                tool_type=self.agent.config.tool_type,
                resources=new_resources,
                context_patterns=context_patterns,
                mcp_servers=new_mcp_servers,
                settings=self.agent.config.settings,
                created_at=self.agent.config.created_at
            )
            
            # Update allowed tools in settings
            new_config.settings.allowed_tools = current_allowed_tools
            
            updated_agent = Agent(config=new_config)
            
            if self.agent_service.update_agent(updated_agent):
                if updated_agent.tool_type == ToolType.Q_CLI:
                    self.agent_service.export_to_q_cli(updated_agent)
                
                self.show_notification(f"Saved agent: {self.agent.name}", "information")
                self.app.pop_screen()
            else:
                self.show_notification("Failed to save agent", "error")
                
        except Exception as e:
            logger.error(f"Error saving agent: {e}", exc_info=True)
            self.show_notification(f"Error: {e}", "error")
    
    def action_cancel(self) -> None:
        """Cancel editing and go back."""
        self.app.pop_screen()
