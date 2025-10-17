"""Main menu screen for AI Agent Manager TUI."""
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, OptionList
from textual.widgets.option_list import Option
from textual.binding import Binding

from ai_configurator.version import __title__
from ai_configurator.tui.screens.base import BaseScreen
from ai_configurator.services.agent_service import AgentService
from ai_configurator.services.library_service import LibraryService
from ai_configurator.services.registry_service import RegistryService


class MainMenuScreen(BaseScreen):
    """Main menu dashboard with system overview and navigation."""
    
    BINDINGS = [
        Binding("1", "agents", "Agents"),
        Binding("2", "library", "Library"),
        Binding("3", "mcp", "MCP Servers"),
        Binding("4", "settings", "Settings"),
        Binding("escape", "quit", "Quit"),
    ]
    
    def compose(self) -> ComposeResult:
        """Build screen layout."""
        yield Header()
        yield Container(
            Static(f"[bold cyan]{__title__}[/bold cyan]\n", id="title"),
            Static(self.get_status_text(), id="status"),
            Vertical(
                OptionList(
                    Option("Agent Management", id="agents"),
                    Option("Library Management", id="library"),
                    Option("MCP Servers", id="mcp"),
                    Option("Settings", id="settings"),
                    id="menu"
                ),
                id="menu-container"
            ),
            Static("\n[dim]Use arrow keys to navigate, Enter to select, or use number keys 1-4[/dim]", id="help"),
            id="main-container"
        )
        yield Footer()
    
    def get_status_text(self) -> str:
        """Get system status summary."""
        try:
            from ai_configurator.tui.config import get_agents_dir, get_library_paths, get_registry_dir
            
            agent_service = AgentService(get_agents_dir())
            base_path, personal_path = get_library_paths()
            library_service = LibraryService(base_path, personal_path)
            registry_service = RegistryService(get_registry_dir())
            
            agents = agent_service.list_agents()
            library = library_service.create_library()
            servers = registry_service.get_installed_servers()
            
            file_count = len(library.files)
            
            return f"""
[bold]System Status:[/bold]
  Agents: {len(agents)}
  Library Files: {file_count}
  MCP Servers: {len(servers)}
"""
        except Exception as e:
            return f"[yellow]Status unavailable: {e}[/yellow]"
    
    def refresh_data(self) -> None:
        """Refresh status display."""
        status_widget = self.query_one("#status", Static)
        status_widget.update(self.get_status_text())
    
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle menu selection."""
        option_id = event.option.id
        
        if option_id == "agents":
            self.action_agents()
        elif option_id == "library":
            self.action_library()
        elif option_id == "mcp":
            self.action_mcp()
        elif option_id == "settings":
            self.action_settings()
    
    def action_agents(self) -> None:
        """Navigate to agent management."""
        from ai_configurator.tui.screens.agent_manager import AgentManagerScreen
        self.app.push_screen(AgentManagerScreen())
    
    def action_library(self) -> None:
        """Navigate to library management."""
        from ai_configurator.tui.screens.library_manager import LibraryManagerScreen
        self.app.push_screen(LibraryManagerScreen())
    
    def action_mcp(self) -> None:
        """Navigate to MCP management."""
        from ai_configurator.tui.screens.mcp_manager import MCPManagerScreen
        self.app.push_screen(MCPManagerScreen())
    
    def action_settings(self) -> None:
        """Navigate to settings."""
        from ai_configurator.tui.screens.settings import SettingsScreen
        self.app.push_screen(SettingsScreen())
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
