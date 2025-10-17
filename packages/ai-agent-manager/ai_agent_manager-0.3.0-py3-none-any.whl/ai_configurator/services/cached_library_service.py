"""
Performance-optimized library service with caching and lazy loading.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from functools import lru_cache

from rich.console import Console

from ..models.library import Library, LibraryMetadata
from ..models.value_objects import LibrarySource


@dataclass
class CachedLibraryFile:
    """Cached library file with content and metadata."""
    path: str
    content: str
    metadata: Dict[str, Any]
    last_modified: datetime
    content_hash: str
    source: LibrarySource = LibrarySource.BASE
    _from_cache: bool = False
    _lazy_loaded: bool = False


@dataclass
class CacheEntry:
    """Cache entry for library files."""
    file_path: str
    content_hash: str
    metadata: Dict[str, Any]
    content: Optional[str] = None
    last_accessed: datetime = None
    last_modified: datetime = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = datetime.now()
        if self.last_modified is None:
            self.last_modified = datetime.now()


class CachedLibraryService:
    """Performance-optimized library service with intelligent caching."""
    
    def __init__(self, cache_dir: Optional[Path] = None, console: Optional[Console] = None):
        self.console = console or Console()
        self.cache_dir = cache_dir or Path.home() / ".config" / "ai-configurator" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory caches
        self._file_cache: Dict[str, CacheEntry] = {}
        self._metadata_cache: Dict[str, LibraryMetadata] = {}
        self._directory_cache: Dict[str, Tuple[List[str], datetime]] = {}
        
        # Cache configuration
        self.max_memory_cache_size = 50  # Keep 50 most recent files in memory
        self.cache_ttl_hours = 24  # Cache valid for 24 hours
        self.lazy_load_threshold = 10  # Load content only when needed for files > 10KB
        
        # Load persistent cache
        self._load_persistent_cache()
    
    def get_library_files(self, library_paths: List[Path], force_refresh: bool = False) -> List[CachedLibraryFile]:
        """Get library files with intelligent caching."""
        start_time = time.time()
        
        all_files = []
        cache_hits = 0
        cache_misses = 0
        
        for library_path in library_paths:
            if not library_path.exists():
                continue
            
            # Check directory cache first
            dir_key = str(library_path)
            cached_files, cache_time = self._directory_cache.get(dir_key, ([], datetime.min))
            
            # Refresh directory cache if needed
            if force_refresh or self._is_cache_expired(cache_time):
                file_paths = self._scan_directory(library_path)
                self._directory_cache[dir_key] = (file_paths, datetime.now())
                cache_misses += 1
            else:
                file_paths = cached_files
                cache_hits += 1
            
            # Process each file
            for file_path in file_paths:
                full_path = library_path / file_path
                library_file = self._get_cached_file(full_path, force_refresh)
                
                if library_file:
                    all_files.append(library_file)
                    if hasattr(library_file, '_from_cache'):
                        cache_hits += 1
                    else:
                        cache_misses += 1
        
        elapsed = time.time() - start_time
        
        self.console.print(f"📊 Performance: {len(all_files)} files loaded in {elapsed:.2f}s "
                          f"(Cache: {cache_hits} hits, {cache_misses} misses)")
        
        return all_files
    
    def _scan_directory(self, directory: Path) -> List[str]:
        """Scan directory for markdown files."""
        files = []
        
        for file_path in directory.rglob("*.md"):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(directory))
                files.append(relative_path)
        
        return sorted(files)
    
    def _get_cached_file(self, file_path: Path, force_refresh: bool = False) -> Optional[CachedLibraryFile]:
        """Get file with caching support."""
        cache_key = str(file_path)
        
        # Check if file exists
        if not file_path.exists():
            return None
        
        # Get file stats
        stat = file_path.stat()
        current_hash = self._calculate_file_hash(file_path)
        
        # Check memory cache
        if not force_refresh and cache_key in self._file_cache:
            cache_entry = self._file_cache[cache_key]
            
            # Validate cache entry
            if cache_entry.content_hash == current_hash:
                cache_entry.last_accessed = datetime.now()
                
                # Create library file from cache
                library_file = self._create_library_file_from_cache(cache_entry, file_path)
                library_file._from_cache = True
                return library_file
        
        # Load file from disk
        try:
            content = file_path.read_text(encoding='utf-8')
            metadata = self._extract_metadata(content)
            
            # Determine if we should lazy load content
            should_lazy_load = stat.st_size > (self.lazy_load_threshold * 1024)
            
            # Create cache entry
            cache_entry = CacheEntry(
                file_path=cache_key,
                content_hash=current_hash,
                metadata=metadata,
                content=None if should_lazy_load else content,
                last_modified=datetime.fromtimestamp(stat.st_mtime)
            )
            
            # Store in memory cache
            self._store_in_memory_cache(cache_key, cache_entry)
            
            # Create library file
            library_file = CachedLibraryFile(
                path=str(file_path.relative_to(file_path.parent.parent)),
                content=content,
                metadata=metadata,
                last_modified=cache_entry.last_modified,
                content_hash=current_hash
            )
            
            # Mark as lazy loaded if content was not cached
            if should_lazy_load:
                library_file._lazy_loaded = True
            
            return library_file
            
        except Exception as e:
            self.console.print(f"⚠️  Failed to load {file_path}: {e}")
            return None
    
    def _store_in_memory_cache(self, cache_key: str, cache_entry: CacheEntry) -> None:
        """Store entry in memory cache with LRU eviction."""
        self._file_cache[cache_key] = cache_entry
        
        # Implement LRU eviction
        if len(self._file_cache) > self.max_memory_cache_size:
            # Sort by last accessed time and remove oldest
            sorted_entries = sorted(
                self._file_cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # Remove oldest entries
            entries_to_remove = len(self._file_cache) - self.max_memory_cache_size
            for i in range(entries_to_remove):
                key_to_remove = sorted_entries[i][0]
                del self._file_cache[key_to_remove]
    
    def _create_library_file_from_cache(self, cache_entry: CacheEntry, file_path: Path) -> CachedLibraryFile:
        """Create CachedLibraryFile from cache entry."""
        # Load content if not cached (lazy loading)
        content = cache_entry.content
        if content is None:
            content = file_path.read_text(encoding='utf-8')
            cache_entry.content = content  # Cache for next time
        
        return CachedLibraryFile(
            path=str(file_path.relative_to(file_path.parent.parent)),
            content=content,
            metadata=cache_entry.metadata,
            last_modified=cache_entry.last_modified,
            content_hash=cache_entry.content_hash
        )
    
    @lru_cache(maxsize=256)
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash with LRU caching."""
        try:
            # Use file size and mtime for quick hash
            stat = file_path.stat()
            quick_hash = f"{stat.st_size}:{stat.st_mtime}"
            return hashlib.md5(quick_hash.encode()).hexdigest()
        except Exception:
            return ""
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from file content."""
        metadata = {
            "version": "1.0.0",  # Default version for compatibility
            "title": "",
            "tags": [],
            "description": "",
            "word_count": len(content.split()),
            "line_count": len(content.splitlines())
        }
        
        lines = content.splitlines()
        if not lines:
            return metadata
        
        # Extract title from first heading
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('# '):
                metadata["title"] = line[2:].strip()
                break
        
        # Extract tags from content (simple implementation)
        import re
        tag_pattern = r'#(\w+)'
        tags = re.findall(tag_pattern, content)
        metadata["tags"] = list(set(tags))  # Remove duplicates
        
        return metadata
    
    def _is_cache_expired(self, cache_time: datetime) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() - cache_time > timedelta(hours=self.cache_ttl_hours)
    
    def _load_persistent_cache(self) -> None:
        """Load cache from disk."""
        cache_file = self.cache_dir / "library_cache.json"
        
        if not cache_file.exists():
            return
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Restore cache entries
            for key, entry_data in cache_data.get("file_cache", {}).items():
                # Convert datetime strings back to datetime objects
                entry_data["last_accessed"] = datetime.fromisoformat(entry_data["last_accessed"])
                entry_data["last_modified"] = datetime.fromisoformat(entry_data["last_modified"])
                
                self._file_cache[key] = CacheEntry(**entry_data)
            
            # Restore directory cache
            for key, (files, cache_time_str) in cache_data.get("directory_cache", {}).items():
                cache_time = datetime.fromisoformat(cache_time_str)
                self._directory_cache[key] = (files, cache_time)
                
        except Exception as e:
            self.console.print(f"⚠️  Failed to load cache: {e}")
    
    def save_persistent_cache(self) -> None:
        """Save cache to disk."""
        cache_file = self.cache_dir / "library_cache.json"
        
        try:
            # Prepare cache data for serialization
            cache_data = {
                "file_cache": {},
                "directory_cache": {}
            }
            
            # Convert file cache
            for key, entry in self._file_cache.items():
                entry_dict = asdict(entry)
                # Convert datetime objects to strings
                entry_dict["last_accessed"] = entry.last_accessed.isoformat()
                entry_dict["last_modified"] = entry.last_modified.isoformat()
                # Don't persist content to save space
                entry_dict["content"] = None
                cache_data["file_cache"][key] = entry_dict
            
            # Convert directory cache
            for key, (files, cache_time) in self._directory_cache.items():
                cache_data["directory_cache"][key] = (files, cache_time.isoformat())
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            self.console.print(f"⚠️  Failed to save cache: {e}")
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        self._file_cache.clear()
        self._metadata_cache.clear()
        self._directory_cache.clear()
        
        # Clear LRU cache
        self._calculate_file_hash.cache_clear()
        
        # Remove persistent cache
        cache_file = self.cache_dir / "library_cache.json"
        if cache_file.exists():
            cache_file.unlink()
        
        self.console.print("✅ Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "memory_cache_size": len(self._file_cache),
            "max_memory_cache_size": self.max_memory_cache_size,
            "directory_cache_size": len(self._directory_cache),
            "cache_ttl_hours": self.cache_ttl_hours,
            "lazy_load_threshold_kb": self.lazy_load_threshold,
            "lru_cache_info": self._calculate_file_hash.cache_info()._asdict()
        }
    
    def optimize_cache(self) -> None:
        """Optimize cache by removing expired entries."""
        now = datetime.now()
        expired_keys = []
        
        # Find expired file cache entries
        for key, entry in self._file_cache.items():
            if now - entry.last_accessed > timedelta(hours=self.cache_ttl_hours):
                expired_keys.append(key)
        
        # Remove expired entries
        for key in expired_keys:
            del self._file_cache[key]
        
        # Find expired directory cache entries
        expired_dir_keys = []
        for key, (files, cache_time) in self._directory_cache.items():
            if self._is_cache_expired(cache_time):
                expired_dir_keys.append(key)
        
        for key in expired_dir_keys:
            del self._directory_cache[key]
        
        self.console.print(f"🧹 Cache optimized: removed {len(expired_keys)} file entries, "
                          f"{len(expired_dir_keys)} directory entries")
    
    def preload_library(self, library_paths: List[Path]) -> None:
        """Preload library files into cache."""
        self.console.print("🔄 Preloading library cache...")
        
        start_time = time.time()
        files_loaded = 0
        
        for library_path in library_paths:
            if not library_path.exists():
                continue
            
            file_paths = self._scan_directory(library_path)
            
            for file_path in file_paths:
                full_path = library_path / file_path
                self._get_cached_file(full_path)
                files_loaded += 1
        
        elapsed = time.time() - start_time
        self.console.print(f"✅ Preloaded {files_loaded} files in {elapsed:.2f}s")
        
        # Save cache to disk
        self.save_persistent_cache()
