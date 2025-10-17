"""Configuration helper for TUI."""
from pathlib import Path


def get_config_dir() -> Path:
    """Get the configuration directory."""
    config_dir = Path.home() / ".config" / "ai-configurator"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_agents_dir() -> Path:
    """Get the agents directory."""
    agents_dir = get_config_dir() / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    return agents_dir


def get_library_paths() -> tuple[Path, Path]:
    """Get library base and personal paths."""
    config_dir = get_config_dir()
    base_path = config_dir / "library" / "base"
    personal_path = config_dir / "library" / "personal"
    base_path.mkdir(parents=True, exist_ok=True)
    personal_path.mkdir(parents=True, exist_ok=True)
    return base_path, personal_path


def get_registry_dir() -> Path:
    """Get the MCP registry directory."""
    # Use 'registry' for backward compatibility with existing data
    registry_dir = get_config_dir() / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)
    return registry_dir
