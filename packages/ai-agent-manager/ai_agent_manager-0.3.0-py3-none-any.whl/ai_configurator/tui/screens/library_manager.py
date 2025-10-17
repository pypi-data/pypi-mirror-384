"""Library management screen."""
import logging
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Button, Static, DataTable
from textual.binding import Binding

from ai_configurator.tui.screens.base import BaseScreen
from ai_configurator.services.library_service import LibraryService
from ai_configurator.services.sync_service import SyncService

logger = logging.getLogger(__name__)


class LibraryManagerScreen(BaseScreen):
    """Library synchronization interface."""
    
    BINDINGS = [
        Binding("n", "new_file", "New"),
        Binding("e", "edit_file", "Edit"),
        Binding("c", "clone_file", "Clone"),
        Binding("o", "open_folder", "Open Folder"),
        Binding("s", "sync", "Sync"),
        Binding("d", "diff", "Diff"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    def __init__(self):
        super().__init__()
        from ai_configurator.tui.config import get_library_paths
        base_path, personal_path = get_library_paths()
        self.library_service = LibraryService(base_path, personal_path)
        self.sync_service = SyncService()
        self.selected_file = None
        self.personal_path = personal_path
        self.library_root_path = personal_path.parent  # Store library root
    
    def compose(self) -> ComposeResult:
        """Build screen layout."""
        yield Header()
        yield Container(
            Static("[bold cyan]Library Management[/bold cyan]\n[dim]n=New e=Edit c=Clone o=Open Folder s=Sync d=Diff r=Refresh[/dim]", id="title"),
            Static(self.get_status_text(), id="status"),
            DataTable(id="file_table", classes="file-list"),
            id="library-container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize table and load data."""
        table = self.query_one(DataTable)
        table.add_columns("File", "Path", "Size")
        table.cursor_type = "row"
        table.focus()
        self.refresh_data()
    
    def get_status_text(self) -> str:
        """Get library status."""
        try:
            # Count all .md files in library
            total_files = len(list(self.library_root_path.rglob("*.md")))
            
            return f"""[bold]Library Status:[/bold]
  Total Files: {total_files}  Location: {self.library_root_path}"""
        except Exception as e:
            logger.error(f"Error getting status: {e}", exc_info=True)
            return f"[yellow]Status unavailable: {e}[/yellow]"
    
    def refresh_data(self) -> None:
        """Refresh status and file list."""
        # Update status
        status_widget = self.query_one("#status", Static)
        status_widget.update(self.get_status_text())
        
        # Update file table
        table = self.query_one(DataTable)
        table.clear()
        
        try:
            # Scan entire library folder for all .md files
            from collections import defaultdict
            files_by_folder = defaultdict(list)
            
            for md_file in self.library_root_path.rglob("*.md"):
                if md_file.is_file():
                    # Get folder path relative to library root
                    relative_path = md_file.relative_to(self.library_root_path)
                    folder = str(relative_path.parent)
                    
                    files_by_folder[folder].append({
                        'name': md_file.name,
                        'path': str(relative_path),
                        'size': md_file.stat().st_size
                    })
            
            # Sort folders and display
            for folder in sorted(files_by_folder.keys()):
                # Add folder header
                table.add_row(f"[bold cyan]{folder}/[/bold cyan]", "", "")
                
                # Add files in this folder
                for file_info in sorted(files_by_folder[folder], key=lambda x: x['name']):
                    filename = file_info['name']
                    full_path = file_info['path']
                    size = f"{file_info['size']} bytes" if file_info['size'] > 0 else "-"
                    table.add_row(f"  {filename}", full_path, size)
                
                # Add separator between folders
                table.add_row("", "", "")
                
        except Exception as e:
            logger.error(f"Error loading files: {e}", exc_info=True)
            self.show_notification(f"Error loading files: {e}", "error")
    
    def action_sync(self) -> None:
        """Start library synchronization."""
        try:
            from ai_configurator.models.sync_models import LibrarySync
            from ai_configurator.tui.config import get_config_dir
            
            self.show_notification("Syncing library...", "information")
            
            # Create LibrarySync object
            library = self.library_service.create_library()
            backup_path = get_config_dir() / "backups"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            library_sync = LibrarySync(
                base_path=library.base_path,
                personal_path=library.personal_path,
                backup_path=backup_path
            )
            
            result = self.sync_service.sync_library(library_sync, interactive=False)
            
            if result.conflicts_detected > 0:
                self.show_notification(f"Found {result.conflicts_detected} conflicts", "warning")
            else:
                self.show_notification("Sync completed successfully", "information")
            
            self.refresh_data()
        except Exception as e:
            self.show_notification(f"Sync error: {e}", "error")
    
    def action_diff(self) -> None:
        """Show differences."""
        try:
            from ai_configurator.models.sync_models import LibrarySync
            from ai_configurator.tui.config import get_config_dir
            
            library = self.library_service.create_library()
            backup_path = get_config_dir() / "backups"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            library_sync = LibrarySync(
                base_path=library.base_path,
                personal_path=library.personal_path,
                backup_path=backup_path
            )
            
            conflicts = self.sync_service.detect_conflicts(library_sync)
            if conflicts:
                msg = f"Found {len(conflicts)} differences:\n"
                for conflict in conflicts[:5]:  # Show first 5
                    msg += f"  - {conflict.file_path} ({conflict.conflict_type.value})\n"
                if len(conflicts) > 5:
                    msg += f"  ... and {len(conflicts) - 5} more"
                self.show_notification(msg, "information")
            else:
                self.show_notification("No differences found", "information")
        except Exception as e:
            logger.error(f"Error detecting differences: {e}", exc_info=True)
            self.show_notification(f"Error: {e}", "error")
    
    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Track selected file."""
        try:
            table = self.query_one(DataTable)
            if event.cursor_row < table.row_count:
                row = table.get_row_at(event.cursor_row)
                filename = str(row[0]).strip()
                full_path = str(row[1]).strip()
                
                # Skip folder headers (bold cyan), empty rows, and indented filenames
                if full_path and not filename.startswith("[bold"):
                    self.selected_file = full_path
        except Exception as e:
            logger.error(f"Error highlighting row: {e}", exc_info=True)
    
    def action_new_file(self) -> None:
        """Create new file in personal library."""
        from textual.widgets import Input, Button, Label
        from textual.screen import ModalScreen
        from textual.containers import Vertical, Horizontal
        
        class FileNameInputScreen(ModalScreen):
            """Filename input screen."""
            
            def compose(self):
                yield Vertical(
                    Label("Enter filename:"),
                    Input(placeholder="my-rules.md", id="filename_input"),
                    Horizontal(
                        Button("Create", variant="primary", id="create_btn"),
                        Button("Cancel", variant="default", id="cancel_btn"),
                        classes="button_row"
                    ),
                    id="input_dialog"
                )
            
            def on_input_submitted(self, event: Input.Submitted):
                if event.input.id == "filename_input":
                    self.dismiss(event.value)
            
            def on_button_pressed(self, event: Button.Pressed):
                if event.button.id == "create_btn":
                    filename_input = self.query_one("#filename_input", Input)
                    self.dismiss(filename_input.value)
                elif event.button.id == "cancel_btn":
                    self.dismiss(None)
        
        def handle_filename(filename: str):
            if not filename or not filename.strip():
                return
            
            import subprocess
            import os
            import shutil
            
            try:
                filename = filename.strip()
                
                # Ensure .md extension
                if not filename.endswith('.md'):
                    filename += '.md'
                
                # Create in personal library
                file_path = self.personal_path / filename
                
                if file_path.exists():
                    self.show_notification(f"File already exists: {filename}", "warning")
                    return
                
                # Create with template
                file_path.write_text(f"# {filename.replace('.md', '').replace('-', ' ').title()}\n\n")
                
                # Open in editor
                editor = os.environ.get('EDITOR')
                if not editor:
                    # Try common editors
                    for e in ['kate', 'vim', 'vi', 'nano']:
                        if shutil.which(e):
                            editor = e
                            break
                
                if not editor:
                    self.show_notification("No editor found. Set $EDITOR environment variable.", "error")
                    return
                
                subprocess.run([editor, str(file_path)])
                
                self.show_notification(f"Created: {filename}", "information")
                self.refresh_data()
                
            except Exception as e:
                logger.error(f"Error creating file: {e}", exc_info=True)
                self.show_notification(f"Error: {e}", "error")
        
        self.app.push_screen(FileNameInputScreen(), handle_filename)
    
    def action_edit_file(self) -> None:
        """Edit selected file."""
        import subprocess
        import os
        import shutil
        
        if not self.selected_file:
            self.show_notification("No file selected", "warning")
            return
        
        try:
            # Build full path from library root
            file_path = self.library_root_path / self.selected_file
            
            if not file_path.exists():
                self.show_notification(f"File does not exist: {self.selected_file}", "error")
                return
            
            # Check if it's in personal folder - only allow editing personal files
            if not str(file_path).startswith(str(self.personal_path)):
                self.show_notification("Can only edit personal files - press 'c' to clone first", "warning")
                return
            
            # Open in editor
            editor = os.environ.get('EDITOR')
            if not editor:
                # Try common editors
                for e in ['kate', 'vim', 'vi', 'nano']:
                    if shutil.which(e):
                        editor = e
                        break
            
            if not editor:
                self.show_notification("No editor found. Set $EDITOR environment variable.", "error")
                return
            
            logger.info(f"Opening editor: {editor} {file_path}")
            subprocess.run([editor, str(file_path)])
            
            self.show_notification(f"Edited: {self.selected_file}", "information")
            self.refresh_data()
            
        except Exception as e:
            logger.error(f"Error editing file: {e}", exc_info=True)
            self.show_notification(f"Error: {e}", "error")
    
    def action_clone_file(self) -> None:
        """Clone selected file to personal library."""
        import shutil
        from pathlib import Path
        
        if not self.selected_file:
            self.show_notification("No file selected", "warning")
            return
        
        try:
            # Build source path from library root
            source_path = self.library_root_path / self.selected_file
            
            if not source_path.exists():
                self.show_notification(f"File not found: {self.selected_file}", "error")
                return
            
            # Check if already in personal
            if str(source_path).startswith(str(self.personal_path)):
                self.show_notification("File is already in personal library", "warning")
                return
            
            # Target path - preserve relative structure within personal
            relative_to_base = Path(self.selected_file).relative_to(Path(self.selected_file).parts[0])
            target_path = self.personal_path / relative_to_base
            
            if target_path.exists():
                self.show_notification(f"Already exists in personal: {relative_to_base}", "warning")
                return
            
            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, target_path)
            
            self.show_notification(f"Cloned to personal: {relative_to_base}", "information")
            self.refresh_data()
            
        except Exception as e:
            logger.error(f"Error cloning file: {e}", exc_info=True)
            self.show_notification(f"Error: {e}", "error")

    
    def action_open_folder(self) -> None:
        """Open library folder in system file manager."""
        import subprocess
        import platform
        
        try:
            system = platform.system()
            
            if system == "Linux":
                subprocess.Popen(["xdg-open", str(self.library_root_path)])
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", str(self.library_root_path)])
            elif system == "Windows":
                subprocess.Popen(["explorer", str(self.library_root_path)])
            else:
                self.show_notification(f"Unsupported platform: {system}", "error")
                return
            
            self.show_notification(f"Opening: {self.library_root_path}", "information")
            
        except Exception as e:
            logger.error(f"Error opening folder: {e}", exc_info=True)
            self.show_notification(f"Error: {e}", "error")
