"""Settings screen."""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static

from ai_configurator.tui.screens.base import BaseScreen


class SettingsScreen(BaseScreen):
    """Settings and configuration interface."""
    
    def compose(self) -> ComposeResult:
        """Build screen layout."""
        yield Header()
        yield Container(
            Static("[bold cyan]Settings[/bold cyan]", id="title"),
            Static("""
[bold]General Settings:[/bold]
  Theme: Auto (follows terminal)
  Editor: $EDITOR
  
[bold]Library Settings:[/bold]
  Auto-sync: Disabled
  Conflict resolution: Interactive
  
[bold]MCP Settings:[/bold]
  Registry URL: Default
  Auto-update: Enabled

[dim]Settings management coming soon![/dim]
""", id="settings-content"),
            id="settings-container"
        )
        yield Footer()
