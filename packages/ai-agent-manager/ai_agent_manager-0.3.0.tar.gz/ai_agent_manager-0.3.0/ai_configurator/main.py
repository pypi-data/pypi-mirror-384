"""Main entry point for AI Configurator - routes to TUI or CLI."""
import sys


def main():
    """Main entry point - detects mode and routes accordingly."""
    args = sys.argv[1:]
    
    # If no args or 'tui' command, launch TUI
    if len(args) == 0 or (len(args) == 1 and args[0] == 'tui'):
        try:
            from ai_configurator.tui.app import AIConfiguratorApp
            app = AIConfiguratorApp()
            app.run()
        except ImportError as e:
            print(f"Error: TUI dependencies not installed. Run: pip install textual")
            print(f"Details: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error launching TUI: {e}")
            sys.exit(1)
    else:
        # Run CLI commands
        from ai_configurator.cli_enhanced import cli
        cli()


if __name__ == '__main__':
    main()
