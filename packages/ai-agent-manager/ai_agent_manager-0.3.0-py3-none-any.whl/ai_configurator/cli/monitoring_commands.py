"""
Logging and monitoring CLI commands.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from ..core.logging_config import (
    get_logger, get_error_handler, get_health_checker, 
    setup_production_logging, ProductionLogger
)
from ..core.production_config import get_production_config


@click.group(name="monitoring")
def monitoring_group():
    """Logging and monitoring commands."""
    pass


@monitoring_group.command()
def health():
    """Check system health status."""
    console = Console()
    
    console.print("🏥 [bold]Running System Health Check...[/bold]")
    
    health_checker = get_health_checker()
    health_status = health_checker.check_system_health()
    
    # Overall status
    status_color = "green" if health_status["overall_status"] == "healthy" else "red"
    console.print(f"\n📊 Overall Status: [{status_color}]{health_status['overall_status'].upper()}[/{status_color}]")
    
    # Individual checks
    checks_table = Table(title="Health Checks")
    checks_table.add_column("Component", style="cyan")
    checks_table.add_column("Status", style="white")
    checks_table.add_column("Message", style="dim")
    
    for check_name, check_result in health_status["checks"].items():
        status_icon = "✅" if check_result["healthy"] else "❌"
        status_text = "Healthy" if check_result["healthy"] else "Unhealthy"
        
        checks_table.add_row(
            check_name.title(),
            f"{status_icon} {status_text}",
            check_result["message"]
        )
    
    console.print(checks_table)
    
    # Show failed checks if any
    if "failed_checks" in health_status:
        console.print(f"\n⚠️  [red]Failed Checks: {', '.join(health_status['failed_checks'])}[/red]")


@monitoring_group.command()
@click.option("--lines", "-n", type=int, default=50, help="Number of lines to show")
@click.option("--level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
              help="Filter by log level")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def logs(lines: int, level: str, follow: bool):
    """View application logs."""
    console = Console()
    config = get_production_config()
    
    log_file = config.log_dir / "ai-configurator.log"
    
    if not log_file.exists():
        console.print(f"❌ Log file not found: {log_file}")
        return
    
    console.print(f"📄 [bold]Viewing logs from {log_file}[/bold]")
    
    if follow:
        console.print("Press Ctrl+C to stop following...")
        import subprocess
        try:
            cmd = ["tail", "-f", str(log_file)]
            if lines:
                cmd.extend(["-n", str(lines)])
            subprocess.run(cmd)
        except KeyboardInterrupt:
            console.print("\n👋 Stopped following logs")
    else:
        try:
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
            
            # Filter by level if specified
            if level:
                log_lines = [line for line in log_lines if level in line]
            
            # Show last N lines
            display_lines = log_lines[-lines:] if lines else log_lines
            
            for line in display_lines:
                # Color code log levels
                if "ERROR" in line:
                    console.print(line.strip(), style="red")
                elif "WARNING" in line:
                    console.print(line.strip(), style="yellow")
                elif "INFO" in line:
                    console.print(line.strip(), style="blue")
                else:
                    console.print(line.strip())
                    
        except Exception as e:
            console.print(f"❌ Error reading log file: {e}")


@monitoring_group.command()
@click.option("--lines", "-n", type=int, default=20, help="Number of lines to show")
def errors():
    """View error logs."""
    console = Console()
    config = get_production_config()
    
    error_log = config.log_dir / "errors.log"
    
    if not error_log.exists():
        console.print(f"❌ Error log file not found: {error_log}")
        return
    
    console.print(f"🚨 [bold red]Recent Errors[/bold red]")
    
    try:
        with open(error_log, 'r') as f:
            error_lines = f.readlines()
        
        # Show last N lines
        display_lines = error_lines[-lines:] if lines else error_lines
        
        if not display_lines:
            console.print("✅ [green]No errors found[/green]")
            return
        
        error_text = "".join(display_lines)
        syntax = Syntax(error_text, "text", theme="monokai", line_numbers=True)
        console.print(syntax)
        
    except Exception as e:
        console.print(f"❌ Error reading error log: {e}")


@monitoring_group.command()
def setup():
    """Setup production logging."""
    console = Console()
    
    console.print("🔧 [bold]Setting up production logging...[/bold]")
    
    try:
        setup_production_logging()
        console.print("✅ Production logging configured successfully")
        
        # Test logging
        logger = get_logger("setup_test")
        logger.info("Production logging setup completed")
        
        config = get_production_config()
        console.print(f"📁 Log directory: {config.log_dir}")
        console.print(f"📊 Log level: {config.monitoring.log_level.value}")
        console.print(f"🏗️  Structured logging: {'Enabled' if config.monitoring.structured_logging else 'Disabled'}")
        
    except Exception as e:
        console.print(f"❌ Failed to setup logging: {e}")


@monitoring_group.command()
@click.argument("message")
@click.option("--level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
              default="INFO", help="Log level")
def test_log(message: str, level: str):
    """Test logging system with a message."""
    console = Console()
    
    logger = get_logger("test")
    log_method = getattr(logger, level.lower())
    
    log_method(f"Test log message: {message}")
    
    console.print(f"✅ Test message logged at {level} level")
    console.print(f"📄 Check logs with: ai-config monitoring logs")


@monitoring_group.command()
def stats():
    """Show logging and monitoring statistics."""
    console = Console()
    config = get_production_config()
    
    # Log file statistics
    stats_table = Table(title="Logging Statistics")
    stats_table.add_column("Log File", style="cyan")
    stats_table.add_column("Size", style="white")
    stats_table.add_column("Lines", style="green")
    stats_table.add_column("Last Modified", style="yellow")
    
    log_files = [
        ("Main Log", config.log_dir / "ai-configurator.log"),
        ("Error Log", config.log_dir / "errors.log"),
        ("Structured Log", config.log_dir / "structured.log")
    ]
    
    for name, log_file in log_files:
        if log_file.exists():
            stat = log_file.stat()
            size_mb = stat.st_size / (1024 * 1024)
            
            # Count lines
            try:
                with open(log_file, 'r') as f:
                    line_count = sum(1 for _ in f)
            except:
                line_count = "Unknown"
            
            from datetime import datetime
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            
            stats_table.add_row(
                name,
                f"{size_mb:.2f} MB",
                str(line_count),
                modified
            )
        else:
            stats_table.add_row(name, "Not found", "0", "Never")
    
    console.print(stats_table)
    
    # Configuration info
    env_value = config.environment if isinstance(config.environment, str) else config.environment.value
    log_level_value = config.monitoring.log_level if isinstance(config.monitoring.log_level, str) else config.monitoring.log_level.value
    
    config_info = Panel(
        f"Environment: {env_value}\n"
        f"Log Level: {log_level_value}\n"
        f"Structured Logging: {'Enabled' if config.monitoring.structured_logging else 'Disabled'}\n"
        f"Log Directory: {config.log_dir}",
        title="Configuration",
        border_style="blue"
    )
    
    console.print(config_info)


@monitoring_group.command()
@click.option("--days", type=int, default=7, help="Days of logs to keep")
def cleanup(days: int):
    """Clean up old log files."""
    console = Console()
    config = get_production_config()
    
    console.print(f"🧹 [bold]Cleaning up logs older than {days} days...[/bold]")
    
    from datetime import datetime, timedelta
    import os
    
    cutoff_date = datetime.now() - timedelta(days=days)
    cleaned_files = 0
    total_size = 0
    
    try:
        for log_file in config.log_dir.glob("*.log*"):
            if log_file.is_file():
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    file_size = log_file.stat().st_size
                    log_file.unlink()
                    cleaned_files += 1
                    total_size += file_size
        
        if cleaned_files > 0:
            size_mb = total_size / (1024 * 1024)
            console.print(f"✅ Cleaned {cleaned_files} files, freed {size_mb:.2f} MB")
        else:
            console.print("ℹ️  No old log files found to clean")
            
    except Exception as e:
        console.print(f"❌ Error during cleanup: {e}")


@monitoring_group.command()
@click.option("--format", type=click.Choice(["json", "table"]), default="table",
              help="Output format")
def structured():
    """View structured logs."""
    console = Console()
    config = get_production_config()
    
    structured_log = config.log_dir / "structured.log"
    
    if not structured_log.exists():
        console.print(f"❌ Structured log file not found: {structured_log}")
        return
    
    try:
        import json
        
        with open(structured_log, 'r') as f:
            lines = f.readlines()
        
        if format == "json":
            for line in lines[-20:]:  # Show last 20 entries
                try:
                    log_entry = json.loads(line.strip())
                    console.print_json(data=log_entry)
                except json.JSONDecodeError:
                    continue
        else:
            # Table format
            table = Table(title="Structured Logs")
            table.add_column("Timestamp", style="cyan")
            table.add_column("Level", style="white")
            table.add_column("Logger", style="green")
            table.add_column("Message", style="white")
            
            for line in lines[-20:]:  # Show last 20 entries
                try:
                    log_entry = json.loads(line.strip())
                    table.add_row(
                        log_entry.get("timestamp", ""),
                        log_entry.get("level", ""),
                        log_entry.get("logger", ""),
                        log_entry.get("message", "")[:50] + "..." if len(log_entry.get("message", "")) > 50 else log_entry.get("message", "")
                    )
                except json.JSONDecodeError:
                    continue
            
            console.print(table)
            
    except Exception as e:
        console.print(f"❌ Error reading structured logs: {e}")


def register_monitoring_commands(cli):
    """Register monitoring commands with the main CLI."""
    cli.add_command(monitoring_group)
