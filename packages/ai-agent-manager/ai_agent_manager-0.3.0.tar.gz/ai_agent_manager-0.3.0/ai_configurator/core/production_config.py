"""
Production configuration management with environment-specific settings.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

import yaml
from pydantic import BaseModel, Field


class Environment(str, Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = ""
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class CacheConfig:
    """Cache configuration."""
    enabled: bool = True
    max_memory_size: int = 50
    ttl_hours: int = 24
    lazy_load_threshold_kb: int = 10
    persistent_cache: bool = True


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = ""
    token_expiry_hours: int = 24
    max_login_attempts: int = 5
    rate_limit_per_minute: int = 60
    cors_origins: List[str] = field(default_factory=list)


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enabled: bool = True
    metrics_port: int = 9090
    health_check_port: int = 8080
    log_level: LogLevel = LogLevel.INFO
    structured_logging: bool = True
    trace_sampling_rate: float = 0.1


@dataclass
class LibraryConfig:
    """Library-specific configuration."""
    max_file_size_mb: int = 10
    allowed_extensions: List[str] = field(default_factory=lambda: [".md", ".txt", ".json", ".yaml"])
    sync_interval_minutes: int = 60
    backup_retention_days: int = 30
    git_timeout_seconds: int = 300


class ProductionConfig(BaseModel):
    """Production configuration with environment-specific settings."""
    
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=True)
    
    # Application settings
    app_name: str = Field(default="ai-configurator")
    app_version: str = Field(default="4.0.0")
    bind_host: str = Field(default="127.0.0.1")
    bind_port: int = Field(default=8000)
    
    # Paths
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".config" / "ai-configurator")
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".local" / "share" / "ai-configurator")
    log_dir: Path = Field(default_factory=lambda: Path.home() / ".local" / "share" / "ai-configurator" / "logs")
    
    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    library: LibraryConfig = Field(default_factory=LibraryConfig)
    
    # Environment variables override
    env_prefix: str = Field(default="AI_CONFIG_")
    
    class Config:
        use_enum_values = True
    
    @classmethod
    def from_environment(cls, env: Environment = None) -> "ProductionConfig":
        """Create configuration from environment."""
        if env is None:
            env_name = os.getenv("AI_CONFIG_ENVIRONMENT", "development")
            env = Environment(env_name.lower())
        
        # Load base configuration
        config = cls._get_base_config(env)
        
        # Override with environment variables
        config = cls._apply_env_overrides(config)
        
        # Load from config file if exists
        config = cls._load_from_file(config, env)
        
        return config
    
    @classmethod
    def _get_base_config(cls, env: Environment) -> "ProductionConfig":
        """Get base configuration for environment."""
        if env == Environment.DEVELOPMENT:
            return cls(
                environment=env,
                debug=True,
                monitoring=MonitoringConfig(
                    log_level=LogLevel.DEBUG,
                    trace_sampling_rate=1.0
                ),
                cache=CacheConfig(
                    max_memory_size=20,
                    ttl_hours=1
                )
            )
        
        elif env == Environment.STAGING:
            return cls(
                environment=env,
                debug=False,
                bind_host="0.0.0.0",
                monitoring=MonitoringConfig(
                    log_level=LogLevel.INFO,
                    trace_sampling_rate=0.5
                ),
                cache=CacheConfig(
                    max_memory_size=100,
                    ttl_hours=12
                )
            )
        
        elif env == Environment.PRODUCTION:
            return cls(
                environment=env,
                debug=False,
                bind_host="0.0.0.0",
                monitoring=MonitoringConfig(
                    log_level=LogLevel.WARNING,
                    trace_sampling_rate=0.1
                ),
                cache=CacheConfig(
                    max_memory_size=200,
                    ttl_hours=24
                ),
                security=SecurityConfig(
                    max_login_attempts=3,
                    rate_limit_per_minute=30
                )
            )
        
        elif env == Environment.TEST:
            return cls(
                environment=env,
                debug=True,
                monitoring=MonitoringConfig(
                    enabled=False,
                    log_level=LogLevel.ERROR
                ),
                cache=CacheConfig(
                    enabled=False
                )
            )
        
        else:
            return cls(environment=env)
    
    @classmethod
    def _apply_env_overrides(cls, config: "ProductionConfig") -> "ProductionConfig":
        """Apply environment variable overrides."""
        env_vars = {
            "AI_CONFIG_DEBUG": ("debug", bool),
            "AI_CONFIG_HOST": ("bind_host", str),
            "AI_CONFIG_PORT": ("bind_port", int),
            "AI_CONFIG_LOG_LEVEL": ("monitoring.log_level", LogLevel),
            "AI_CONFIG_CACHE_SIZE": ("cache.max_memory_size", int),
            "AI_CONFIG_CACHE_TTL": ("cache.ttl_hours", int),
            "AI_CONFIG_SECRET_KEY": ("security.secret_key", str),
        }
        
        for env_var, (attr_path, attr_type) in env_vars.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    # Convert value to appropriate type
                    if attr_type == bool:
                        value = value.lower() in ("true", "1", "yes", "on")
                    elif attr_type == int:
                        value = int(value)
                    elif attr_type == LogLevel:
                        value = LogLevel(value.upper())
                    
                    # Set nested attribute
                    cls._set_nested_attr(config, attr_path, value)
                    
                except (ValueError, TypeError):
                    pass  # Ignore invalid values
        
        return config
    
    @classmethod
    def _set_nested_attr(cls, obj: Any, attr_path: str, value: Any) -> None:
        """Set nested attribute using dot notation."""
        parts = attr_path.split(".")
        current = obj
        
        for part in parts[:-1]:
            current = getattr(current, part)
        
        setattr(current, parts[-1], value)
    
    @classmethod
    def _load_from_file(cls, config: "ProductionConfig", env: Environment) -> "ProductionConfig":
        """Load configuration from file."""
        config_file = config.config_dir / f"config-{env.value}.yaml"
        
        if not config_file.exists():
            return config
        
        try:
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
            
            # Merge file configuration
            config_dict = config.dict()
            cls._deep_merge(config_dict, file_config)
            
            return cls(**config_dict)
            
        except Exception:
            return config  # Return original config if file loading fails
    
    @classmethod
    def _deep_merge(cls, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge two dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                cls._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save_to_file(self, env: Environment = None) -> Path:
        """Save configuration to file."""
        if env is None:
            env = self.environment
        
        config_file = self.config_dir / f"config-{env.value}.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and remove computed fields
        config_dict = self.dict()
        config_dict.pop("config_dir", None)
        config_dict.pop("data_dir", None)
        config_dict.pop("log_dir", None)
        
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        return config_file
    
    def validate_production_ready(self) -> List[str]:
        """Validate configuration for production deployment."""
        issues = []
        
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                issues.append("Debug mode should be disabled in production")
            
            if self.security.secret_key == "":
                issues.append("Secret key must be set in production")
            
            if self.monitoring.log_level == LogLevel.DEBUG:
                issues.append("Log level should not be DEBUG in production")
            
            if self.bind_host == "127.0.0.1":
                issues.append("Bind host should be 0.0.0.0 for production deployment")
            
            if self.cache.ttl_hours < 12:
                issues.append("Cache TTL should be at least 12 hours in production")
        
        return issues
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information."""
        return {
            "environment": self.environment.value,
            "debug": self.debug,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "config_loaded_at": datetime.now().isoformat(),
            "paths": {
                "config_dir": str(self.config_dir),
                "data_dir": str(self.data_dir),
                "log_dir": str(self.log_dir)
            }
        }


class ConfigManager:
    """Production configuration manager."""
    
    def __init__(self):
        self._config: Optional[ProductionConfig] = None
    
    def load_config(self, env: Environment = None) -> ProductionConfig:
        """Load configuration for environment."""
        if self._config is None or (env and self._config.environment != env):
            self._config = ProductionConfig.from_environment(env)
        
        return self._config
    
    def get_config(self) -> ProductionConfig:
        """Get current configuration."""
        if self._config is None:
            self._config = ProductionConfig.from_environment()
        
        return self._config
    
    def reload_config(self, env: Environment = None) -> ProductionConfig:
        """Reload configuration from environment."""
        self._config = None
        return self.load_config(env)
    
    def validate_config(self) -> List[str]:
        """Validate current configuration."""
        config = self.get_config()
        return config.validate_production_ready()


# Global configuration manager
_config_manager = ConfigManager()


def get_production_config() -> ProductionConfig:
    """Get production configuration."""
    return _config_manager.get_config()


def reload_production_config(env: Environment = None) -> ProductionConfig:
    """Reload production configuration."""
    return _config_manager.reload_config(env)
