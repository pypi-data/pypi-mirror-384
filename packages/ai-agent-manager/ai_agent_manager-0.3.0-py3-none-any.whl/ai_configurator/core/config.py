"""
Configuration manager for AI Configurator.
"""

from pathlib import Path
from typing import Optional

from ..models import Configuration
from ..services.config_service import ConfigService


class ConfigManager:
    """Manager for configuration operations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".config" / "ai-configurator"
        
        self.config_dir = config_dir
        self.config_service = ConfigService(config_dir)
    
    def load_config(self) -> Configuration:
        """Load configuration."""
        return self.config_service.load_configuration()
    
    def save_config(self, config: Configuration) -> bool:
        """Save configuration."""
        return self.config_service.save_configuration(config)
    
    def create_backup(self, config: Configuration, description: str = "") -> bool:
        """Create backup of configuration."""
        backup_info = self.config_service.create_backup(config, "manual", description)
        if backup_info:
            self.save_config(config)
            return True
        return False


# Global config manager instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> Configuration:
    """Get current configuration."""
    return get_config_manager().load_config()


class ConfigProxy:
    """Proxy for configuration that auto-saves changes."""
    
    def __init__(self):
        self._config = get_config()
        self._manager = get_config_manager()
    
    def __getattr__(self, name):
        return getattr(self._config, name)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            setattr(self._config, name, value)
    
    def save(self):
        """Save configuration changes."""
        self._manager.save_config(self._config)
        
    @property
    def library_path(self):
        """Get library path from config."""
        return self._config.library_config.base_library_path
    
    @property
    def remote_library_url(self):
        """Get remote library URL."""
        return self._config.library_config.remote_library_url
    
    @remote_library_url.setter
    def remote_library_url(self, value):
        """Set remote library URL."""
        self._config.library_config.remote_library_url = value
    
    @property
    def remote_library_path(self):
        """Get remote library path."""
        return self._config.library_config.remote_library_path
    
    @remote_library_path.setter
    def remote_library_path(self, value):
        """Set remote library path."""
        self._config.library_config.remote_library_path = value
