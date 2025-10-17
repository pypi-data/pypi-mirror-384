"""Main TUI application for AI Agent Manager."""
import logging
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer

from ai_configurator.version import __title__
from ai_configurator.tui.screens.main_menu import MainMenuScreen

# Configure logging
log_dir = Path.home() / ".config" / "ai-configurator" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "tui.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AIConfiguratorApp(App):
    """AI Agent Manager TUI Application."""
    
    CSS_PATH = "styles/default.tcss"
    TITLE = __title__
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("?", "help", "Help"),
        Binding("escape", "back", "Back"),
        Binding("ctrl+r", "refresh", "Refresh"),
    ]
    
    def on_mount(self) -> None:
        """Initialize application on startup."""
        try:
            logger.info(f"{__title__} starting")
            self.push_screen(MainMenuScreen())
        except Exception as e:
            logger.error(f"Error mounting app: {e}", exc_info=True)
            raise
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()
    
    def action_refresh(self) -> None:
        """Refresh current screen."""
        if hasattr(self.screen, 'refresh_data'):
            self.screen.refresh_data()
    
    def action_help(self) -> None:
        """Show help screen."""
        from ai_configurator.tui.screens.help import HelpScreen
        self.push_screen(HelpScreen())


if __name__ == '__main__':
    app = AIConfiguratorApp()
    app.run()
