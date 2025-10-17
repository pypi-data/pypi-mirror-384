"""
Simplified file utilities for AI Configurator.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, Union


logger = logging.getLogger(__name__)


def ensure_directory(path: Union[str, Path]) -> bool:
    """Ensure a directory exists, creating it if necessary."""
    try:
        path_obj = Path(path) if isinstance(path, str) else path
        path_obj.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False


def copy_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
    """Copy a file from source to destination."""
    try:
        source_path = Path(source) if isinstance(source, str) else source
        dest_path = Path(destination) if isinstance(destination, str) else destination
        
        # Ensure destination directory exists
        ensure_directory(dest_path.parent)
        
        shutil.copy2(source_path, dest_path)
        return True
    except Exception as e:
        logger.error(f"Error copying file from {source} to {destination}: {e}")
        return False


def read_file(path: Union[str, Path]) -> Optional[str]:
    """Read file content as string."""
    try:
        path_obj = Path(path) if isinstance(path, str) else path
        with open(path_obj, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return None


def write_file(path: Union[str, Path], content: str) -> bool:
    """Write content to file."""
    try:
        path_obj = Path(path) if isinstance(path, str) else path
        
        # Ensure directory exists
        ensure_directory(path_obj.parent)
        
        with open(path_obj, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing file {path}: {e}")
        return False
