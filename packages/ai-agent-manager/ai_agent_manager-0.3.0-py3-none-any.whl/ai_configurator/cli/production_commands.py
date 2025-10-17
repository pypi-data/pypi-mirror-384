"""
Production configuration management CLI commands.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from ..core.production_config import (
    Environment, ProductionConfig, get_production_config, 
    reload_production_config, LogLevel
)


@click.group(name="production")
def production_group():
    """Production configuration management commands."""
    pass


@production_group.command()
@click.option("--env", "-e", type=click.Choice(["development", "staging", "production", "test"]),
              help="Environment to show config for")
def show(env: str):
    """Show production configuration."""
    console = Console()
    
    if env:
        config = ProductionConfig.from_environment(Environment(env))
    else:
        config = get_production_config()
    
    # Environment info
    env_info = config.get_environment_info()
    
    console.print(Panel.fit(
        f"[bold blue]{env_info['app_name']} v{env_info['app_version']}[/bold blue]\n"
        f"Environment: [bold]{env_info['environment']}[/bold]\n"
        f"Debug Mode: {'[red]Enabled[/red]' if env_info['debug'] else '[green]Disabled[/green]'}\n"
        f"Config Dir: {env_info['paths']['config_dir']}\n"
        f"Data Dir: {env_info['paths']['data_dir']}\n"
        f"Log Dir: {env_info['paths']['log_dir']}",
        title="Production Configuration"
    ))
    
    # Application settings
    app_table = Table(title="Application Settings")
    app_table.add_column("Setting", style="cyan")
    app_table.add_column("Value", style="white")
    
    app_table.add_row("Bind Host", config.bind_host)
    app_table.add_row("Bind Port", str(config.bind_port))
    app_table.add_row("Environment", config.environment.value)
    app_table.add_row("Debug", str(config.debug))
    
    console.print(app_table)
    
    # Monitoring settings
    monitoring_table = Table(title="Monitoring & Logging")
    monitoring_table.add_column("Setting", style="cyan")
    monitoring_table.add_column("Value", style="white")
    
    monitoring_table.add_row("Enabled", str(config.monitoring.enabled))
    monitoring_table.add_row("Log Level", config.monitoring.log_level.value)
    monitoring_table.add_row("Structured Logging", str(config.monitoring.structured_logging))
    monitoring_table.add_row("Metrics Port", str(config.monitoring.metrics_port))
    monitoring_table.add_row("Health Check Port", str(config.monitoring.health_check_port))
    monitoring_table.add_row("Trace Sampling Rate", str(config.monitoring.trace_sampling_rate))
    
    console.print(monitoring_table)
    
    # Cache settings
    cache_table = Table(title="Cache Configuration")
    cache_table.add_column("Setting", style="cyan")
    cache_table.add_column("Value", style="white")
    
    cache_table.add_row("Enabled", str(config.cache.enabled))
    cache_table.add_row("Max Memory Size", str(config.cache.max_memory_size))
    cache_table.add_row("TTL Hours", str(config.cache.ttl_hours))
    cache_table.add_row("Lazy Load Threshold (KB)", str(config.cache.lazy_load_threshold_kb))
    cache_table.add_row("Persistent Cache", str(config.cache.persistent_cache))
    
    console.print(cache_table)


@production_group.command()
@click.option("--env", "-e", type=click.Choice(["development", "staging", "production", "test"]),
              required=True, help="Environment to validate")
def validate(env: str):
    """Validate configuration for production deployment."""
    console = Console()
    
    config = ProductionConfig.from_environment(Environment(env))
    issues = config.validate_production_ready()
    
    if not issues:
        console.print(f"✅ [green]Configuration for {env} is production-ready[/green]")
    else:
        console.print(f"⚠️  [yellow]Found {len(issues)} issues in {env} configuration:[/yellow]")
        for i, issue in enumerate(issues, 1):
            console.print(f"   {i}. {issue}")


@production_group.command()
@click.option("--env", "-e", type=click.Choice(["development", "staging", "production", "test"]),
              required=True, help="Environment to generate config for")
@click.option("--force", is_flag=True, help="Overwrite existing config file")
def generate(env: str, force: bool):
    """Generate configuration file for environment."""
    console = Console()
    
    environment = Environment(env)
    config = ProductionConfig.from_environment(environment)
    
    config_file = config.config_dir / f"config-{env}.yaml"
    
    if config_file.exists() and not force:
        if not Confirm.ask(f"Config file {config_file} exists. Overwrite?"):
            console.print("❌ Operation cancelled")
            return
    
    try:
        saved_file = config.save_to_file(environment)
        console.print(f"✅ Configuration saved to {saved_file}")
        
        # Show validation results
        issues = config.validate_production_ready()
        if issues:
            console.print(f"\n⚠️  [yellow]Configuration has {len(issues)} issues:[/yellow]")
            for issue in issues:
                console.print(f"   • {issue}")
        else:
            console.print("\n✅ [green]Configuration is production-ready[/green]")
            
    except Exception as e:
        console.print(f"❌ Failed to save configuration: {e}")


@production_group.command()
@click.option("--env", "-e", type=click.Choice(["development", "staging", "production", "test"]),
              help="Environment to set (default: current)")
@click.option("--host", help="Bind host")
@click.option("--port", type=int, help="Bind port")
@click.option("--debug/--no-debug", help="Enable/disable debug mode")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
              help="Log level")
def configure(env: str, host: str, port: int, debug: bool, log_level: str):
    """Configure production settings."""
    console = Console()
    
    if env:
        config = ProductionConfig.from_environment(Environment(env))
        console.print(f"📝 Configuring {env} environment")
    else:
        config = get_production_config()
        console.print(f"📝 Configuring {config.environment.value} environment")
    
    changes_made = False
    
    if host is not None:
        config.bind_host = host
        console.print(f"✅ Bind host set to {host}")
        changes_made = True
    
    if port is not None:
        config.bind_port = port
        console.print(f"✅ Bind port set to {port}")
        changes_made = True
    
    if debug is not None:
        config.debug = debug
        console.print(f"✅ Debug mode {'enabled' if debug else 'disabled'}")
        changes_made = True
    
    if log_level is not None:
        config.monitoring.log_level = LogLevel(log_level)
        console.print(f"✅ Log level set to {log_level}")
        changes_made = True
    
    if changes_made:
        try:
            config.save_to_file()
            console.print(f"\n💾 Configuration saved")
        except Exception as e:
            console.print(f"\n❌ Failed to save configuration: {e}")
    else:
        console.print("ℹ️  No changes specified")


@production_group.command()
def environments():
    """List all available environments and their configurations."""
    console = Console()
    
    table = Table(title="Environment Configurations")
    table.add_column("Environment", style="cyan")
    table.add_column("Debug", style="white")
    table.add_column("Host", style="white")
    table.add_column("Port", style="white")
    table.add_column("Log Level", style="yellow")
    table.add_column("Cache Size", style="green")
    table.add_column("Status", style="magenta")
    
    for env in Environment:
        config = ProductionConfig.from_environment(env)
        issues = config.validate_production_ready()
        
        status = "✅ Ready" if not issues else f"⚠️  {len(issues)} issues"
        
        table.add_row(
            env.value,
            str(config.debug),
            config.bind_host,
            str(config.bind_port),
            config.monitoring.log_level.value,
            str(config.cache.max_memory_size),
            status
        )
    
    console.print(table)


@production_group.command()
@click.option("--env", "-e", type=click.Choice(["development", "staging", "production", "test"]),
              help="Environment to check")
def health(env: str):
    """Check production health and readiness."""
    console = Console()
    
    if env:
        config = ProductionConfig.from_environment(Environment(env))
    else:
        config = get_production_config()
    
    console.print(f"🏥 [bold]Health Check: {config.environment.value}[/bold]")
    
    # Check configuration
    issues = config.validate_production_ready()
    config_status = "✅ Healthy" if not issues else f"⚠️  {len(issues)} issues"
    
    # Check paths
    paths_ok = all([
        config.config_dir.exists(),
        config.data_dir.parent.exists(),  # Parent should exist
        config.log_dir.parent.exists()    # Parent should exist
    ])
    paths_status = "✅ Accessible" if paths_ok else "❌ Issues"
    
    # Create health table
    health_table = Table()
    health_table.add_column("Component", style="cyan")
    health_table.add_column("Status", style="white")
    health_table.add_column("Details", style="dim")
    
    health_table.add_row("Configuration", config_status, f"{len(issues)} validation issues")
    health_table.add_row("File Paths", paths_status, "Config, data, and log directories")
    health_table.add_row("Environment", "✅ Set", config.environment.value)
    health_table.add_row("Debug Mode", 
                        "⚠️  Enabled" if config.debug else "✅ Disabled",
                        "Should be disabled in production")
    
    console.print(health_table)
    
    if issues:
        console.print(f"\n⚠️  [yellow]Configuration Issues:[/yellow]")
        for issue in issues:
            console.print(f"   • {issue}")


def register_production_commands(cli):
    """Register production commands with the main CLI."""
    cli.add_command(production_group)
