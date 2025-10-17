"""Q CLI agent import screen."""
import logging
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Button, DataTable, Static, Label
from textual.binding import Binding
from textual.screen import ModalScreen

from ai_configurator.tui.screens.base import BaseScreen
from ai_configurator.services.qcli_sync_service import QCLISyncService

logger = logging.getLogger(__name__)


class ResourcePromptScreen(ModalScreen[bool]):
    """Modal screen to ask user about resource path handling."""
    
    def __init__(self, resource_path: Path):
        super().__init__()
        self.resource_path = resource_path
        self.apply_to_all = False
    
    def compose(self) -> ComposeResult:
        """Build modal layout."""
        yield Container(
            Label(f"[bold]External Resource Found[/bold]\n\n{self.resource_path}\n\nHow should this file be handled?"),
            Button("Copy to Library", id="copy", variant="primary"),
            Button("Keep Absolute Path", id="keep"),
            Button("Apply to All Remaining", id="apply_all"),
            id="resource-prompt"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "copy":
            self.dismiss(True)
        elif event.button.id == "keep":
            self.dismiss(False)
        elif event.button.id == "apply_all":
            self.apply_to_all = True
            self.dismiss(True)


class QCLIImportScreen(BaseScreen):
    """Q CLI agent import interface."""
    
    BINDINGS = [
        Binding("space", "toggle_select", "Select"),
        Binding("a", "select_all", "Select All"),
        Binding("i", "import_selected", "Import"),
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self):
        super().__init__()
        from ai_configurator.tui.config import get_agents_dir, get_registry_dir, get_library_paths
        
        qcli_dir = Path.home() / ".aws" / "amazonq" / "cli-agents"
        local_dir = get_agents_dir()
        registry_dir = get_registry_dir()
        base_path, personal_path = get_library_paths()
        library_dir = base_path.parent  # Get library root
        
        self.sync_service = QCLISyncService(qcli_dir, local_dir, registry_dir, library_dir)
        self.selected_agents = set()
        self.copy_to_library_choice = None  # For "apply to all"
    
    def compose(self) -> ComposeResult:
        """Build screen layout."""
        yield Header()
        yield Container(
            Static("[bold cyan]Import Agents from Q CLI[/bold cyan]\n[dim]Space=Select a=Select All i=Import Esc=Cancel[/dim]", id="title"),
            DataTable(id="import_table"),
            Static("", id="status"),
            id="import-container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize table and load data."""
        table = self.query_one(DataTable)
        table.add_columns("", "Agent Name", "Status")
        table.cursor_type = "row"
        table.focus()
        self.refresh_data()
    
    def refresh_data(self) -> None:
        """Refresh agent list."""
        table = self.query_one(DataTable)
        
        # Save cursor position
        cursor_row = table.cursor_row if table.cursor_row is not None else 0
        
        table.clear()
        
        # Get importable agents
        importable = self.sync_service.list_importable_agents()
        conflicting = self.sync_service.list_conflicting_agents()
        
        for agent_name in importable:
            checkbox = "[X]" if agent_name in self.selected_agents else "[ ]"
            table.add_row(checkbox, agent_name, "[green]New[/green]")
        
        for agent_name in conflicting:
            checkbox = "[X]" if agent_name in self.selected_agents else "[ ]"
            table.add_row(checkbox, agent_name, "[yellow]Exists (will merge)[/yellow]")
        
        # Restore cursor position
        if table.row_count > 0:
            table.move_cursor(row=min(cursor_row, table.row_count - 1))
        
        # Update status
        status = self.query_one("#status", Static)
        total = len(importable) + len(conflicting)
        selected = len(self.selected_agents)
        status.update(f"[dim]{selected}/{total} selected[/dim]")
    
    def action_toggle_select(self) -> None:
        """Toggle selection of current agent."""
        table = self.query_one(DataTable)
        if table.cursor_row is None:
            return
        
        row_data = table.get_row_at(table.cursor_row)
        agent_name = row_data[1]  # Second column is agent name
        
        if agent_name in self.selected_agents:
            self.selected_agents.remove(agent_name)
        else:
            self.selected_agents.add(agent_name)
        
        self.refresh_data()
    
    def action_select_all(self) -> None:
        """Select all agents."""
        importable = self.sync_service.list_importable_agents()
        conflicting = self.sync_service.list_conflicting_agents()
        self.selected_agents = set(importable + conflicting)
        self.refresh_data()
    
    async def action_import_selected(self) -> None:
        """Import selected agents."""
        if not self.selected_agents:
            self.notify("No agents selected", severity="warning")
            return
        
        status = self.query_one("#status", Static)
        status.update("[yellow]Importing...[/yellow]")
        
        success_count = 0
        fail_count = 0
        errors = []
        
        for agent_name in self.selected_agents:
            try:
                success, message = self.sync_service.import_agent(
                    agent_name,
                    self._ask_copy_to_library
                )
                
                if success:
                    success_count += 1
                    logger.info(message)
                else:
                    fail_count += 1
                    errors.append(f"{agent_name}: {message}")
                    logger.error(message)
            except Exception as e:
                fail_count += 1
                error_msg = f"{agent_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to import {agent_name}: {e}", exc_info=True)
        
        # Show result
        if fail_count == 0:
            self.notify(f"✓ Imported {success_count} agent(s)", severity="information")
        else:
            error_summary = "\n".join(errors[:3])  # Show first 3 errors
            if len(errors) > 3:
                error_summary += f"\n... and {len(errors) - 3} more"
            self.notify(f"Imported {success_count}, failed {fail_count}\n{error_summary}", severity="error", timeout=10)
        
        # Return to agent management
        self.app.pop_screen()
    
    def action_cancel(self) -> None:
        """Cancel import."""
        self.app.pop_screen()
    
    async def _ask_copy_to_library(self, resource_path: Path) -> bool:
        """Ask user whether to copy resource to library.
        
        Args:
            resource_path: Path to the resource file
            
        Returns:
            True to copy, False to keep absolute path
        """
        # If user chose "apply to all", use that choice
        if self.copy_to_library_choice is not None:
            return self.copy_to_library_choice
        
        # Show modal prompt
        result = await self.app.push_screen_wait(ResourcePromptScreen(resource_path))
        
        # Check if user chose "apply to all"
        prompt_screen = self.app.screen_stack[-1]
        if isinstance(prompt_screen, ResourcePromptScreen) and prompt_screen.apply_to_all:
            self.copy_to_library_choice = result
        
        return result
