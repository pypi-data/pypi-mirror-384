"""
File management service for local file discovery and monitoring.
"""

import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
from rich.console import Console

from ..models.file_models import (
    FilePattern, LocalResource, FileWatcher, FileWatchConfig, FileDiscoveryResult
)
from ..models.value_objects import LibrarySource


class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events."""
    
    def __init__(self, file_service: 'FileService', agent_id: str):
        self.file_service = file_service
        self.agent_id = agent_id
        self.debounce_timer: Optional[threading.Timer] = None
        self.pending_changes: set = set()
    
    def on_modified(self, event):
        if not event.is_directory:
            self._handle_change(event.src_path, 'modified')
    
    def on_created(self, event):
        if not event.is_directory:
            self._handle_change(event.src_path, 'created')
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._handle_change(event.src_path, 'deleted')
    
    def _handle_change(self, file_path: str, change_type: str):
        """Handle file change with debouncing."""
        self.pending_changes.add((file_path, change_type))
        
        # Cancel existing timer
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        # Start new timer
        self.debounce_timer = threading.Timer(
            1.0,  # 1 second debounce
            self._process_changes
        )
        self.debounce_timer.start()
    
    def _process_changes(self):
        """Process accumulated changes."""
        changes = list(self.pending_changes)
        self.pending_changes.clear()
        
        for file_path, change_type in changes:
            self.file_service._handle_file_change(self.agent_id, Path(file_path), change_type)


class FileService:
    """Service for managing local file discovery and monitoring."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.observers: Dict[str, Observer] = {}
        self.watchers: Dict[str, FileWatcher] = {}
        self.change_callbacks: Dict[str, List[Callable]] = {}
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        if not file_path.exists():
            return ""
        
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ""
    
    def discover_files(self, patterns: List[FilePattern]) -> FileDiscoveryResult:
        """Discover files matching the given patterns."""
        result = FileDiscoveryResult()
        
        for pattern in patterns:
            try:
                resolved_pattern = pattern.resolve_pattern()
                base_path = pattern.base_path
                
                # Use glob to find matching files
                if pattern.recursive:
                    glob_pattern = pattern.pattern
                    if not glob_pattern.startswith('./'):
                        glob_pattern = f"**/{glob_pattern}"
                else:
                    glob_pattern = pattern.pattern
                
                # Search from base path
                for file_path in base_path.glob(glob_pattern):
                    if file_path.is_file():
                        # Check extension
                        if not pattern.matches_extension(file_path):
                            continue
                        
                        # Check exclusions
                        if pattern.is_excluded(file_path):
                            result.add_excluded(file_path)
                            continue
                        
                        result.add_file(file_path, pattern.pattern)
                
            except Exception as e:
                result.add_error(f"Error processing pattern '{pattern.pattern}': {e}")
        
        return result
    
    def create_local_resource(self, file_path: Path, base_path: Path) -> Optional[LocalResource]:
        """Create a LocalResource from a file path."""
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            relative_path = str(file_path.relative_to(base_path))
            content_hash = self.calculate_file_hash(file_path)
            
            return LocalResource(
                file_path=file_path,
                relative_path=relative_path,
                content_hash=content_hash,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
                source=LibrarySource.LOCAL
            )
        except Exception:
            return None
    
    def start_watching(self, agent_id: str, watcher: FileWatcher) -> bool:
        """Start watching files for an agent."""
        if agent_id in self.observers:
            self.stop_watching(agent_id)
        
        try:
            observer = Observer()
            handler = FileChangeHandler(self, agent_id)
            
            # Watch directories containing the patterns
            watched_dirs = set()
            for pattern in watcher.watch_config.patterns:
                watch_dir = pattern.base_path
                if watch_dir not in watched_dirs:
                    observer.schedule(handler, str(watch_dir), recursive=pattern.recursive)
                    watched_dirs.add(watch_dir)
            
            observer.start()
            self.observers[agent_id] = observer
            self.watchers[agent_id] = watcher
            watcher.is_active = True
            
            self.console.print(f"✅ Started watching files for agent: {agent_id}")
            return True
            
        except Exception as e:
            self.console.print(f"❌ Failed to start watching for agent {agent_id}: {e}")
            return False
    
    def stop_watching(self, agent_id: str) -> bool:
        """Stop watching files for an agent."""
        if agent_id in self.observers:
            try:
                observer = self.observers[agent_id]
                observer.stop()
                observer.join()
                del self.observers[agent_id]
                
                if agent_id in self.watchers:
                    self.watchers[agent_id].is_active = False
                
                self.console.print(f"✅ Stopped watching files for agent: {agent_id}")
                return True
            except Exception as e:
                self.console.print(f"❌ Failed to stop watching for agent {agent_id}: {e}")
                return False
        return True
    
    def _handle_file_change(self, agent_id: str, file_path: Path, change_type: str):
        """Handle a file change event."""
        watcher = self.watchers.get(agent_id)
        if not watcher:
            return
        
        # Check if this file matches any of our patterns
        matches_pattern = False
        for pattern in watcher.watch_config.patterns:
            try:
                if file_path.match(pattern.pattern) and pattern.matches_extension(file_path):
                    if not pattern.is_excluded(file_path):
                        matches_pattern = True
                        break
            except Exception:
                continue
        
        if not matches_pattern:
            return
        
        if change_type == 'deleted':
            watcher.remove_file(file_path)
            self.console.print(f"🗑️  File removed from watch: {file_path}")
        else:
            # File created or modified
            if file_path.exists():
                stat = file_path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                content_hash = self.calculate_file_hash(file_path)
                
                existing_resource = watcher.get_file(file_path)
                if existing_resource:
                    # Update existing resource
                    if existing_resource.needs_update(mtime, content_hash):
                        watcher.update_file(file_path, mtime, content_hash, stat.st_size)
                        self.console.print(f"🔄 File updated: {file_path}")
                        self._notify_change_callbacks(agent_id, file_path, 'updated')
                else:
                    # Add new resource if auto-add is enabled
                    if watcher.watch_config.auto_add_new_files:
                        resource = self.create_local_resource(file_path, pattern.base_path)
                        if resource:
                            watcher.add_file(resource)
                            self.console.print(f"➕ New file added to watch: {file_path}")
                            self._notify_change_callbacks(agent_id, file_path, 'added')
    
    def add_change_callback(self, agent_id: str, callback: Callable):
        """Add a callback for file changes."""
        if agent_id not in self.change_callbacks:
            self.change_callbacks[agent_id] = []
        self.change_callbacks[agent_id].append(callback)
    
    def _notify_change_callbacks(self, agent_id: str, file_path: Path, change_type: str):
        """Notify registered callbacks of file changes."""
        callbacks = self.change_callbacks.get(agent_id, [])
        for callback in callbacks:
            try:
                callback(file_path, change_type)
            except Exception as e:
                self.console.print(f"⚠️  Callback error: {e}")
    
    def scan_for_changes(self, agent_id: str) -> List[LocalResource]:
        """Manually scan for file changes."""
        watcher = self.watchers.get(agent_id)
        if not watcher:
            return []
        
        changed_files = []
        for resource in watcher.watched_files.values():
            if resource.file_path.exists():
                stat = resource.file_path.stat()
                current_mtime = datetime.fromtimestamp(stat.st_mtime)
                current_hash = self.calculate_file_hash(resource.file_path)
                
                if resource.needs_update(current_mtime, current_hash):
                    resource.update_metadata(current_mtime, current_hash, stat.st_size)
                    changed_files.append(resource)
        
        watcher.last_scan = datetime.now()
        return changed_files
    
    def get_watch_status(self, agent_id: str) -> Dict:
        """Get watching status for an agent."""
        watcher = self.watchers.get(agent_id)
        observer = self.observers.get(agent_id)
        
        return {
            "agent_id": agent_id,
            "is_watching": agent_id in self.observers,
            "is_active": watcher.is_active if watcher else False,
            "watched_files_count": len(watcher.watched_files) if watcher else 0,
            "patterns_count": len(watcher.watch_config.patterns) if watcher else 0,
            "last_scan": watcher.last_scan if watcher else None
        }
    
    def cleanup(self):
        """Stop all watchers and cleanup resources."""
        for agent_id in list(self.observers.keys()):
            self.stop_watching(agent_id)
        self.change_callbacks.clear()
