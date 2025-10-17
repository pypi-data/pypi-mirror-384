"""
Comprehensive logging and error handling for production use.
"""

import logging
import logging.handlers
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

import json
from rich.console import Console
from rich.logging import RichHandler

from .production_config import get_production_config, LogLevel, Environment


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for production logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry)


class ProductionLogger:
    """Production-ready logger with structured logging and error handling."""
    
    def __init__(self, name: str = "ai-configurator"):
        self.name = name
        self.config = get_production_config()
        self.console = Console()
        self._loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration based on environment."""
        # Create log directory
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.monitoring.log_level.value))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add console handler for development
        if self.config.environment == Environment.DEVELOPMENT:
            console_handler = RichHandler(
                console=self.console,
                show_time=True,
                show_path=True,
                rich_tracebacks=True
            )
            console_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(console_handler)
        
        # Add file handlers for all environments
        self._add_file_handlers(root_logger)
        
        # Add structured logging for production
        if self.config.monitoring.structured_logging:
            self._add_structured_handler(root_logger)
    
    def _add_file_handlers(self, logger: logging.Logger) -> None:
        """Add rotating file handlers."""
        # Main log file
        main_log = self.config.log_dir / "ai-configurator.log"
        main_handler = logging.handlers.RotatingFileHandler(
            main_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        main_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(main_handler)
        
        # Error log file
        error_log = self.config.log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'Function: %(funcName)s (%(filename)s:%(lineno)d)\n'
            '%(message)s\n'
        ))
        logger.addHandler(error_handler)
    
    def _add_structured_handler(self, logger: logging.Logger) -> None:
        """Add structured JSON logging handler."""
        structured_log = self.config.log_dir / "structured.log"
        structured_handler = logging.handlers.RotatingFileHandler(
            structured_log,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5
        )
        structured_handler.setFormatter(StructuredFormatter())
        logger.addHandler(structured_handler)
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get logger instance."""
        logger_name = name or self.name
        
        if logger_name not in self._loggers:
            self._loggers[logger_name] = logging.getLogger(logger_name)
        
        return self._loggers[logger_name]
    
    def log_with_context(self, level: int, message: str, **context) -> None:
        """Log message with additional context."""
        logger = self.get_logger()
        
        # Create log record with extra fields
        record = logger.makeRecord(
            logger.name, level, "", 0, message, (), None
        )
        record.extra_fields = context
        
        logger.handle(record)


class ErrorHandler:
    """Comprehensive error handling for production use."""
    
    def __init__(self, logger: ProductionLogger = None):
        self.logger = logger or ProductionLogger()
        self.config = get_production_config()
    
    def handle_exception(self, exc: Exception, context: Dict[str, Any] = None) -> None:
        """Handle exception with logging and context."""
        logger = self.logger.get_logger("error_handler")
        
        error_context = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "environment": self.config.environment if isinstance(self.config.environment, str) else self.config.environment.value,
            **(context or {})
        }
        
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            exc_info=True,
            extra={"extra_fields": error_context}
        )
    
    def handle_critical_error(self, message: str, exc: Exception = None, 
                            context: Dict[str, Any] = None) -> None:
        """Handle critical errors that may require immediate attention."""
        logger = self.logger.get_logger("critical")
        
        error_context = {
            "critical": True,
            "environment": self.config.environment if isinstance(self.config.environment, str) else self.config.environment.value,
            "timestamp": datetime.now().isoformat(),
            **(context or {})
        }
        
        if exc:
            error_context.update({
                "exception_type": type(exc).__name__,
                "exception_message": str(exc)
            })
        
        logger.critical(
            f"CRITICAL ERROR: {message}",
            exc_info=exc is not None,
            extra={"extra_fields": error_context}
        )
        
        # In production, you might want to send alerts here
        if self.config.environment == Environment.PRODUCTION:
            self._send_alert(message, error_context)
    
    def _send_alert(self, message: str, context: Dict[str, Any]) -> None:
        """Send alert for critical errors (placeholder for actual implementation)."""
        # This would integrate with your alerting system
        # e.g., Slack, PagerDuty, email, etc.
        pass


def log_exceptions(logger_name: str = None):
    """Decorator to log exceptions from functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = ProductionLogger().get_logger(logger_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Exception in {func.__name__}: {e}",
                    exc_info=True,
                    extra={
                        "extra_fields": {
                            "function": func.__name__,
                            "module": func.__module__,
                            "args_count": len(args),
                            "kwargs_keys": list(kwargs.keys())
                        }
                    }
                )
                raise
        return wrapper
    return decorator


def log_performance(logger_name: str = None, threshold_seconds: float = 1.0):
    """Decorator to log performance metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            logger = ProductionLogger().get_logger(logger_name or f"{func.__module__}.performance")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if execution_time > threshold_seconds:
                    logger.warning(
                        f"Slow execution: {func.__name__} took {execution_time:.2f}s",
                        extra={
                            "extra_fields": {
                                "function": func.__name__,
                                "execution_time": execution_time,
                                "threshold": threshold_seconds,
                                "performance_issue": True
                            }
                        }
                    )
                else:
                    logger.debug(
                        f"Performance: {func.__name__} took {execution_time:.2f}s",
                        extra={
                            "extra_fields": {
                                "function": func.__name__,
                                "execution_time": execution_time
                            }
                        }
                    )
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Exception in {func.__name__} after {execution_time:.2f}s: {e}",
                    exc_info=True,
                    extra={
                        "extra_fields": {
                            "function": func.__name__,
                            "execution_time": execution_time,
                            "failed": True
                        }
                    }
                )
                raise
        return wrapper
    return decorator


@contextmanager
def error_context(operation: str, **context):
    """Context manager for error handling with operation context."""
    error_handler = ErrorHandler()
    logger = error_handler.logger.get_logger("context")
    
    operation_context = {
        "operation": operation,
        "start_time": datetime.now().isoformat(),
        **context
    }
    
    logger.info(f"Starting operation: {operation}", extra={"extra_fields": operation_context})
    
    try:
        yield
        logger.info(f"Completed operation: {operation}", extra={"extra_fields": operation_context})
    except Exception as e:
        operation_context.update({
            "failed": True,
            "error": str(e),
            "error_type": type(e).__name__
        })
        error_handler.handle_exception(e, operation_context)
        raise


class HealthChecker:
    """Health check system for monitoring application status."""
    
    def __init__(self):
        self.logger = ProductionLogger().get_logger("health")
        self.config = get_production_config()
    
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.config.environment if isinstance(self.config.environment, str) else self.config.environment.value,
            "overall_status": "healthy",
            "checks": {}
        }
        
        # Check file system
        health_status["checks"]["filesystem"] = self._check_filesystem()
        
        # Check configuration
        health_status["checks"]["configuration"] = self._check_configuration()
        
        # Check logging
        health_status["checks"]["logging"] = self._check_logging()
        
        # Check memory usage
        health_status["checks"]["memory"] = self._check_memory()
        
        # Determine overall status
        failed_checks = [
            name for name, check in health_status["checks"].items()
            if not check.get("healthy", False)
        ]
        
        if failed_checks:
            health_status["overall_status"] = "unhealthy"
            health_status["failed_checks"] = failed_checks
        
        self.logger.info(
            f"Health check completed: {health_status['overall_status']}",
            extra={"extra_fields": health_status}
        )
        
        return health_status
    
    def _check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem health."""
        try:
            # Check if required directories exist and are writable
            directories = [
                self.config.config_dir,
                self.config.data_dir,
                self.config.log_dir
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                
                # Test write access
                test_file = directory / ".health_check"
                test_file.write_text("health_check")
                test_file.unlink()
            
            return {"healthy": True, "message": "Filesystem accessible"}
            
        except Exception as e:
            return {"healthy": False, "message": f"Filesystem error: {e}"}
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration health."""
        try:
            issues = self.config.validate_production_ready()
            
            if issues:
                return {
                    "healthy": False,
                    "message": f"Configuration issues: {len(issues)}",
                    "issues": issues
                }
            else:
                return {"healthy": True, "message": "Configuration valid"}
                
        except Exception as e:
            return {"healthy": False, "message": f"Configuration error: {e}"}
    
    def _check_logging(self) -> Dict[str, Any]:
        """Check logging system health."""
        try:
            # Test log writing
            test_logger = self.logger
            test_logger.info("Health check test log entry")
            
            return {"healthy": True, "message": "Logging system operational"}
            
        except Exception as e:
            return {"healthy": False, "message": f"Logging error: {e}"}
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent > 90:
                return {
                    "healthy": False,
                    "message": f"High memory usage: {memory_percent}%",
                    "memory_percent": memory_percent
                }
            else:
                return {
                    "healthy": True,
                    "message": f"Memory usage normal: {memory_percent}%",
                    "memory_percent": memory_percent
                }
                
        except ImportError:
            return {"healthy": True, "message": "Memory monitoring not available (psutil not installed)"}
        except Exception as e:
            return {"healthy": False, "message": f"Memory check error: {e}"}


# Global instances
_production_logger = None
_error_handler = None
_health_checker = None


def get_logger(name: str = None) -> logging.Logger:
    """Get production logger instance."""
    global _production_logger
    if _production_logger is None:
        _production_logger = ProductionLogger()
    return _production_logger.get_logger(name)


def get_error_handler() -> ErrorHandler:
    """Get error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def get_health_checker() -> HealthChecker:
    """Get health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def setup_production_logging() -> None:
    """Setup production logging (call this at application startup)."""
    global _production_logger
    _production_logger = ProductionLogger()
    
    # Setup global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_handler = get_error_handler()
        error_handler.handle_critical_error(
            "Unhandled exception",
            exc_value,
            {
                "exc_type": exc_type.__name__,
                "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback)
            }
        )
    
    sys.excepthook = handle_exception
