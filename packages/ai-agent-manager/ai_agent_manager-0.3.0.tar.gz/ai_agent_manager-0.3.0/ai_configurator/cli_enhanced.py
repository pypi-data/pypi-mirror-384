"""Enhanced CLI interface with simplified resource-based commands."""
import click
from click_default_group import DefaultGroup

from ai_configurator.cli.agent_commands import agent
from ai_configurator.cli.library_commands import library
from ai_configurator.cli.mcp_commands import mcp
from ai_configurator.cli.system_commands import init, status, health, logs, stats, tui


@click.group(cls=DefaultGroup, default='status', default_if_no_args=False)
@click.version_option(version='4.0.0', prog_name='ai-config')
def cli():
    """AI Configurator v4.0 - Tool-agnostic knowledge library manager with TUI.
    
    Launch TUI: ai-config (no arguments)
    Run commands: ai-config <resource> <action>
    """
    pass


# Register command groups
cli.add_command(agent)
cli.add_command(library)
cli.add_command(mcp)

# Register system commands
cli.add_command(init)
cli.add_command(status)
cli.add_command(health)
cli.add_command(logs)
cli.add_command(stats)
cli.add_command(tui)


def main():
    """Entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
