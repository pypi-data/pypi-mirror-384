"""Help screen."""
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static

from ai_configurator.tui.screens.base import BaseScreen


class HelpScreen(BaseScreen):
    """Help and keyboard shortcuts reference."""
    
    def compose(self) -> ComposeResult:
        """Build screen layout."""
        yield Header()
        yield Container(
            Static("[bold cyan]Help & Keyboard Shortcuts[/bold cyan]", id="title"),
            Vertical(
                Static("""
[bold]Global Shortcuts:[/bold]
  q           - Quit application
  ?           - Show this help
  Escape      - Go back / Cancel
  Ctrl+R      - Refresh current screen
  F5          - Refresh data

[bold]Navigation:[/bold]
  1           - Agent Management
  2           - Library Management
  3           - MCP Servers
  4           - Settings
  Tab         - Move between elements
  Enter       - Select / Confirm

[bold]Agent Management:[/bold]
  n           - New agent
  e           - Edit selected agent
  d           - Delete selected agent
  x           - Export selected agent

[bold]Library Management:[/bold]
  s           - Sync library
  d           - Show differences
  u           - Update from base

[bold]MCP Management:[/bold]
  b           - Browse registry
  i           - Install server
  c           - Configure server

[dim]Press Escape to close this help[/dim]
""", id="help-content"),
                id="help-scroll"
            ),
            id="help-container"
        )
        yield Footer()
