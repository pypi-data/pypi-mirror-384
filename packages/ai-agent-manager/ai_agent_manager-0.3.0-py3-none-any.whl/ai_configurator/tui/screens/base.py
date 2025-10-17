"""Base screen class for all TUI screens."""
from textual.screen import Screen
from textual.binding import Binding


class BaseScreen(Screen):
    """Base class for all TUI screens."""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loading = False
        self.error_message = None
    
    def refresh_data(self) -> None:
        """Refresh screen data. Override in subclasses."""
        pass
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_refresh(self) -> None:
        """Refresh current screen data."""
        self.refresh_data()
    
    def show_notification(self, message: str, severity: str = "information") -> None:
        """Show notification to user."""
        self.app.notify(message, severity=severity)
