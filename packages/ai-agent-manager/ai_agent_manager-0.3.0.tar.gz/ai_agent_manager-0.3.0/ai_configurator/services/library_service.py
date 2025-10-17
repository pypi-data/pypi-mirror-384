"""
Library service for managing knowledge files and synchronization.
"""

import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models import (
    Library, LibraryFile, LibraryMetadata, ConflictInfo,
    LibrarySource, ConflictType, Resolution, SyncStatus
)


class LibraryService:
    """Service for library operations and conflict resolution."""
    
    def __init__(self, base_path: Path, personal_path: Path):
        self.base_path = base_path
        self.personal_path = personal_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.personal_path.mkdir(parents=True, exist_ok=True)
        self._ensure_templates()
    
    def _ensure_templates(self) -> None:
        """Ensure templates directory exists with default templates."""
        templates_dir = self.base_path / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy templates from source if available
        import ai_configurator
        source_templates = Path(ai_configurator.__file__).parent.parent / "library" / "templates"
        
        if source_templates.exists():
            # Copy any missing templates
            for template_file in source_templates.glob("*.md"):
                dest_file = templates_dir / template_file.name
                if not dest_file.exists():
                    shutil.copy2(template_file, dest_file)
        elif not any(templates_dir.glob("*.md")):
            # Only create defaults if no templates exist at all
            self._create_default_templates(templates_dir)
    
    def _create_default_templates(self, templates_dir: Path) -> None:
        """Create default templates."""
        templates = {
            "system-administrator-q-cli.md": """# System Administrator

System administration focused AI assistant for infrastructure management and operations.

## Responsibilities
- Server management and monitoring
- System security and compliance  
- Infrastructure automation
- Performance optimization

## Skills
- Linux/Unix administration
- Network configuration
- Security best practices
- Automation scripting
""",
            "software-engineer-q-cli.md": """# Software Engineer

Software development focused AI assistant for coding and engineering tasks.

## Responsibilities
- Software design and development
- Code review and quality
- Testing and debugging
- Technical documentation

## Skills
- Programming languages
- Software architecture
- Version control
- Testing methodologies
""",
            "daily-assistant-q-cli.md": """# Daily Assistant

General productivity AI assistant for daily tasks and support.

## Responsibilities
- Task planning and organization
- Information research
- Communication assistance
- Problem-solving support

## Skills
- Task management
- Research and analysis
- Clear communication
- Process improvement
"""
        }
        
        for filename, content in templates.items():
            (templates_dir / filename).write_text(content)
    
    def create_library(self) -> Library:
        """Create a new library instance with indexed files."""
        # Index base library files
        base_files = self._index_files(self.base_path, LibrarySource.BASE)
        
        # Index personal library files
        personal_files = self._index_files(self.personal_path, LibrarySource.PERSONAL)
        
        # Combine all files
        all_files = {}
        all_files.update(base_files)
        all_files.update(personal_files)
        
        # Detect conflicts
        conflicts = self._detect_conflicts(base_files, personal_files)
        
        # Create metadata
        metadata = LibraryMetadata(
            version="4.0.0",
            last_sync=datetime.now(),
            base_hash=self._calculate_library_hash(base_files),
            personal_hash=self._calculate_library_hash(personal_files),
            conflicts=conflicts,
            sync_status=SyncStatus.CONFLICTS if conflicts else SyncStatus.SYNCED
        )
        
        return Library(
            base_path=self.base_path,
            personal_path=self.personal_path,
            metadata=metadata,
            files=all_files
        )
    
    def sync_library(self, library: Library) -> List[ConflictInfo]:
        """Synchronize library and detect conflicts."""
        conflicts = []
        
        # Index base library files
        base_files = self._index_files(self.base_path, LibrarySource.BASE)
        
        # Index personal library files
        personal_files = self._index_files(self.personal_path, LibrarySource.PERSONAL)
        
        # Update library files
        library.files.update(base_files)
        library.files.update(personal_files)
        
        # Detect conflicts
        conflicts = self._detect_conflicts(base_files, personal_files)
        
        # Update metadata
        library.metadata.conflicts = conflicts
        library.metadata.last_sync = datetime.now()
        library.metadata.sync_status = SyncStatus.CONFLICTS if conflicts else SyncStatus.SYNCED
        library.metadata.base_hash = self._calculate_library_hash(base_files)
        library.metadata.personal_hash = self._calculate_library_hash(personal_files)
        
        return conflicts
    
    def resolve_conflict(self, library: Library, file_path: str, resolution: Resolution) -> bool:
        """Resolve a specific conflict."""
        if not library.resolve_conflict(file_path, resolution):
            return False
        
        # Apply the resolution
        base_file_path = self.base_path / file_path
        personal_file_path = self.personal_path / file_path
        
        if resolution == Resolution.ACCEPT_REMOTE:
            # Copy base file to personal library
            if base_file_path.exists():
                personal_file_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(base_file_path, personal_file_path)
        elif resolution == Resolution.KEEP_LOCAL:
            # Keep personal file as is (no action needed)
            pass
        elif resolution == Resolution.MERGE:
            # For now, merge means keep local (manual merge would be handled externally)
            pass
        
        # Update file in library
        if personal_file_path.exists():
            library_file = self._create_library_file(personal_file_path, LibrarySource.PERSONAL)
            library.files[f"personal/{file_path}"] = library_file
        
        return True
    
    def discover_files(self, library: Library, pattern: str = "**/*.md") -> List[str]:
        """Discover files matching pattern."""
        return library.discover_files(pattern)
    
    def get_file_content(self, library: Library, relative_path: str) -> Optional[str]:
        """Get effective file content with personal override."""
        effective_file = library.get_effective_file(relative_path)
        if not effective_file:
            return None
        
        if effective_file.source == LibrarySource.PERSONAL:
            file_path = self.personal_path / relative_path
        else:
            file_path = self.base_path / relative_path
        
        if file_path.exists():
            return file_path.read_text(encoding='utf-8')
        return None
    
    def save_personal_file(self, library: Library, relative_path: str, content: str) -> bool:
        """Save content to personal library."""
        file_path = self.personal_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            file_path.write_text(content, encoding='utf-8')
            
            # Update library
            library_file = self._create_library_file(file_path, LibrarySource.PERSONAL)
            library.files[f"personal/{relative_path}"] = library_file
            
            return True
        except Exception:
            return False
    
    def _index_files(self, root_path: Path, source: LibrarySource) -> Dict[str, LibraryFile]:
        """Index all files in a directory."""
        files = {}
        
        if not root_path.exists():
            return files
        
        for file_path in root_path.rglob("*.md"):
            if file_path.is_file():
                relative_path = file_path.relative_to(root_path)
                library_file = self._create_library_file(file_path, source, relative_path)
                key = f"{source.value}/{relative_path}"
                files[key] = library_file
        
        return files
    
    def _create_library_file(self, file_path: Path, source: LibrarySource, relative_path: Path = None) -> LibraryFile:
        """Create LibraryFile from filesystem path."""
        content = file_path.read_text(encoding='utf-8')
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Use relative_path if provided, otherwise just the filename
        path_str = str(relative_path) if relative_path else str(file_path.name)
        
        return LibraryFile(
            path=path_str,
            source=source,
            content_hash=content_hash,
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
            size=file_path.stat().st_size
        )
    
    def _detect_conflicts(self, base_files: Dict[str, LibraryFile], 
                         personal_files: Dict[str, LibraryFile]) -> List[ConflictInfo]:
        """Detect conflicts between base and personal libraries."""
        conflicts = []
        
        # Extract relative paths
        base_paths = {f.split('/', 1)[1]: f for f in base_files.keys()}
        personal_paths = {f.split('/', 1)[1]: f for f in personal_files.keys()}
        
        # Check for conflicts
        for rel_path in base_paths:
            if rel_path in personal_paths:
                base_file = base_files[base_paths[rel_path]]
                personal_file = personal_files[personal_paths[rel_path]]
                
                if base_file.content_hash != personal_file.content_hash:
                    conflict = ConflictInfo(
                        file_path=rel_path,
                        base_content_hash=base_file.content_hash,
                        personal_content_hash=personal_file.content_hash,
                        conflict_type=ConflictType.MODIFIED
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _calculate_library_hash(self, files: Dict[str, LibraryFile]) -> str:
        """Calculate hash of entire library state."""
        if not files:
            return ""
        
        # Sort files by path for consistent hashing
        sorted_files = sorted(files.items())
        combined_hash = hashlib.sha256()
        
        for _, file_info in sorted_files:
            combined_hash.update(file_info.content_hash.encode())
        
        return combined_hash.hexdigest()
