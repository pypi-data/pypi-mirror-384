"""Project version and metadata."""
from pathlib import Path
import sys

# Try to get version from package metadata first (for installed packages)
try:
    from importlib.metadata import version, metadata
    __version__ = version("ai-agent-manager")
    pkg_metadata = metadata("ai-agent-manager")
    __title__ = f"AI Agent Manager v{__version__}"
except Exception:
    # Fallback: read from pyproject.toml (for development)
    # Use tomllib for Python 3.11+, tomli for older versions
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomli as tomllib
        except ImportError:
            tomllib = None
    
    if tomllib is not None:
        try:
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                project = data.get("project", {})
                __version__ = project.get("version", "0.0.0")
                __title__ = f"AI Agent Manager v{__version__}"
            else:
                __version__ = "0.0.0"
                __title__ = "AI Agent Manager v0.0.0"
        except Exception:
            __version__ = "0.0.0"
            __title__ = "AI Agent Manager v0.0.0"
    else:
        __version__ = "0.0.0"
        __title__ = "AI Agent Manager v0.0.0"
