"""Logs viewer screen."""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static, TextArea

from ai_configurator.tui.screens.base import BaseScreen


class LogsScreen(BaseScreen):
    """Application logs viewer."""
    
    def compose(self) -> ComposeResult:
        """Build screen layout."""
        yield Header()
        yield Container(
            Static("[bold cyan]Application Logs[/bold cyan]", id="title"),
            TextArea("No logs available yet.\n\nLog viewing will be implemented in a future update.", id="logs-content", read_only=True),
            id="logs-container"
        )
        yield Footer()
