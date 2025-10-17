"""
Configuration service for managing user preferences and backups.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import Configuration, BackupInfo


class ConfigService:
    """Service for configuration management and backup operations."""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_file = config_dir / "config.json"
        self.backup_dir = config_dir / "backups"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def load_configuration(self) -> Configuration:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                return Configuration(**data)
            except Exception:
                # If config is corrupted, create default
                pass
        
        return Configuration()
    
    def save_configuration(self, config: Configuration) -> bool:
        """Save configuration to file."""
        if not config.validate():
            return False
        
        try:
            config.last_updated = datetime.now()
            data = config.dict()
            self.config_file.write_text(json.dumps(data, indent=2, default=str))
            return True
        except Exception:
            return False
    
    def create_backup(self, config: Configuration, backup_type: str = "manual", 
                     description: str = "") -> Optional[BackupInfo]:
        """Create a backup of the current configuration."""
        backup_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{backup_type}_{timestamp}_{backup_id}.json"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Save current config as backup
            backup_data = config.dict()
            backup_content = json.dumps(backup_data, indent=2, default=str)
            backup_path.write_text(backup_content)
            
            # Create backup info
            backup_info = BackupInfo(
                backup_id=backup_id,
                backup_type=backup_type,
                description=description,
                file_path=backup_path,
                size_bytes=len(backup_content.encode())
            )
            
            # Add to configuration
            config.add_backup(backup_info)
            
            return backup_info
        except Exception:
            return None
    
    def restore_backup(self, config: Configuration, backup_id: str) -> bool:
        """Restore configuration from backup."""
        backup_info = config.get_backup(backup_id)
        if not backup_info or not backup_info.file_path.exists():
            return False
        
        try:
            backup_data = json.loads(backup_info.file_path.read_text())
            restored_config = Configuration(**backup_data)
            
            if restored_config.validate():
                # Update current config with restored data
                config.user_preferences = restored_config.user_preferences
                config.sync_settings = restored_config.sync_settings
                config.backup_policy = restored_config.backup_policy
                config.tool_settings = restored_config.tool_settings
                config.last_updated = datetime.now()
                
                return True
        except Exception:
            pass
        
        return False
