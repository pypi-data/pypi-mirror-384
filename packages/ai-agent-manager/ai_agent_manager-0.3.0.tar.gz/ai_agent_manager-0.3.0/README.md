# AI Agent Manager v0.1.0 (Beta)

**Terminal UI for managing AI agents, resources, and MCP servers across multiple AI tools.**

## 🎯 What It Does

AI Agent Manager helps you manage AI agents (Amazon Q CLI, Claude, etc.) with a visual terminal interface:
- 📚 **Library Management**: Organize knowledge files (templates, rules, docs)
- 🤖 **Agent Configuration**: Create and edit AI agents visually
- 🔌 **MCP Server Management**: Add and configure Model Context Protocol servers
- 🎨 **Dual-Pane Editor**: Select resources and MCP servers with checkboxes
- 🔄 **Auto-Export**: Agents automatically export to Q CLI directory

## ✨ Key Features

### 🖥️ **TUI (Terminal User Interface)**
- **Dual-Pane Editor**: Resources on left, agent config on right
- **Multi-Select**: Use Space to select multiple files/servers
- **Keyboard Navigation**: Arrow keys + shortcuts (no mouse needed)
- **Live Preview**: See current agent configuration while editing
- **Auto-Export**: Changes sync to Q CLI automatically

### 📚 **Library System**
- **Base Library**: Shared templates and rules (5 default templates included)
- **Personal Library**: Your custom files
- **Clone & Edit**: Copy base files to personal for customization
- **Visual Separation**: Clear distinction between base and personal files

### 🔌 **MCP Server Management**
- **Paste Configs**: Copy JSON from internet, paste directly
- **Flexible Parsing**: Handles multiple JSON formats
- **Edit Configs**: Modify server settings in your editor
- **Registry**: Browse and add servers from MCP registry

## 📦 Installation

```bash
# Install from PyPI
pip install ai-agent-manager

# Or install from source
git clone https://github.com/jschwellach/ai-configurator.git
cd ai-configurator
pip install -e .
```

## 🚀 Quick Start

### Launch TUI
```bash
ai-agent-manager
# or shorthand:
ai-config

# Navigate with:
#   1 - Agent Management
#   2 - Library Management
#   3 - MCP Servers
#   4 - Settings
#   ? - Help
#   q - Quit
```

### Using CLI (For Automation)
```bash
# Create an agent
ai-config agent create my-agent --tool q-cli

# List agents
ai-config agent list

# Sync library
ai-config library sync

# Browse MCP servers
ai-config mcp browse

# Get help
ai-config --help
```

## 📚 Features

### 🏗️ **Core Features**
- **Tool-Agnostic Library**: Pure markdown knowledge that works with any AI tool
- **Role-Based Organization**: Knowledge organized around roles
- **Multi-Tool Agent Support**: Amazon Q CLI, Claude Projects, ChatGPT (planned)
- **File References**: Agents reference library files without duplication
- **MCP Integration**: Full MCP server management
- **Cross-Platform**: Windows, macOS, and Linux

### 🔄 **Library Management**
- **Synchronization**: Conflict-aware sync between base and personal libraries
- **Local Files**: Include project files using glob patterns
- **Git Integration**: Clone, sync, and collaborate via Git
- **Performance**: Intelligent caching with 3.3x speedup

### 🖥️ **User Experience**
- **TUI Mode**: Visual, menu-driven interface
- **CLI Mode**: Simplified, consistent commands
- **Interactive Wizards**: Step-by-step setup
- **Template System**: Pre-built agent templates

## 📖 Documentation

- [TUI User Guide](docs/TUI_GUIDE.md) - Complete TUI usage guide
- [Migration Guide](docs/MIGRATION_GUIDE_V4.md) - Upgrading from v3.x
- [Keyboard Shortcuts](docs/KEYBOARD_SHORTCUTS.md) - Quick reference
- [User Guide](docs/USER_GUIDE.md) - Comprehensive documentation
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues

## 🎮 Usage Examples

### Agent Management
```bash
# CLI
ai-config agent create my-agent
ai-config agent list
ai-config agent export my-agent

# TUI
ai-config  # Navigate to Agent Management
```

### Library Management
```bash
# CLI
ai-config library status
ai-config library sync
ai-config library files "**/*.md"

# TUI
ai-config  # Navigate to Library Management
```

### MCP Server Management
```bash
# CLI
ai-config mcp browse
ai-config mcp install filesystem
ai-config mcp list

# TUI
ai-config  # Navigate to MCP Servers
```

## 🔑 Key Commands

| Command | Description |
|---------|-------------|
| `ai-config` | Launch TUI |
| `ai-config agent list` | List all agents |
| `ai-config agent create <name>` | Create new agent |
| `ai-config library sync` | Sync library |
| `ai-config mcp browse` | Browse MCP servers |
| `ai-config status` | Show system status |
| `ai-config --help` | Show help |

## 🎯 Quick Start

### Using TUI (Recommended for New Users)
```bash
# Launch TUI
ai-config

# Navigate with:
#   1 - Agent Management
#   2 - Library Management
#   3 - MCP Servers
#   4 - Settings
#   ? - Help
#   q - Quit
```

### Using CLI (For Automation)
```bash
# Create an agent
ai-config agent create my-agent --tool q-cli

# List agents
ai-config agent list

# Sync library
ai-config library sync

# Browse MCP servers
ai-config mcp browse

# Get help
ai-config --help
```
cd ai-configurator
pip install -r requirements-dev.txt
pip install -e .
```

## 🚀 Quick Start

### New User Setup
```bash
# Complete interactive setup for new users
ai-config wizard quick-start

# Or step by step:
ai-config status                    # Check system status
ai-config library sync              # Sync knowledge library
ai-config wizard create-agent       # Create your first agent
```

### Existing Users
```bash
# Check system status
ai-config status

# Sync library with conflict resolution
ai-config library sync

# Browse available MCP servers
ai-config mcp browse

# Create agent from template
ai-config wizard create-agent
```

## 📚 Command Reference

### 🚀 Production Management (Phase 3)
```bash
# Git-based library management
ai-config git clone <repo-url>       # Clone remote library
ai-config git pull                   # Pull updates
ai-config git push                   # Push changes
ai-config git status                 # Show Git status
ai-config git sync                   # Sync with remote

# Enhanced synchronization
ai-config sync all                   # Sync all libraries
ai-config sync source remote         # Sync specific source
ai-config sync status                # Show sync status

# Performance and caching
ai-config cache stats                # Show cache statistics
ai-config cache benchmark            # Run performance test
ai-config cache preload              # Preload cache
ai-config cache clear                # Clear cache

# Production configuration
ai-config production show            # Show config
ai-config production environments    # List environments
ai-config production validate --env production
ai-config production generate --env production

# Monitoring and logging
ai-config monitoring health          # System health check
ai-config monitoring logs            # View logs
ai-config monitoring stats           # Log statistics
ai-config monitoring setup           # Setup logging
```

### 🔄 Library Management
```bash
# Library synchronization
ai-config library status            # Show sync status
ai-config library sync              # Sync with conflict resolution
ai-config library diff              # Show differences
ai-config library update            # Update from base library

# View library content
ai-config status                    # System overview
```

### 📁 File Management
```bash
# Discover and add local files
ai-config files scan-files <agent> --pattern "**/*.md"
ai-config files add-files <agent> --pattern "./docs/**/*.md"
ai-config files watch-files <agent> --enable

# Examples
ai-config files scan-files my-agent --pattern "**/*.py" --base-path .
ai-config files add-files dev-agent --pattern "./rules/**/*.md"
```

### 🔧 MCP Server Management
```bash
# Browse and discover servers
ai-config mcp browse                # Browse available servers
ai-config mcp search git            # Search for specific servers
ai-config mcp status                # Show registry status

# Install and manage servers
ai-config mcp install filesystem    # Install a server
ai-config mcp create-sample         # Create sample registry
```

### 🧙 Interactive Wizards
```bash
# Setup wizards
ai-config wizard quick-start        # Complete new user setup
ai-config wizard create-agent       # Interactive agent creation
ai-config wizard setup-mcp <agent>  # MCP server setup

# Agent management
ai-config create-agent              # Create new agent
ai-config manage-agent <name>       # Interactive management
ai-config export-agent <name> --save  # Export to Q CLI
```

## 🏗️ Architecture

### Library Structure
```
~/.config/ai-configurator/
├── library/                 # Base knowledge library
│   ├── roles/              # Role-specific knowledge
│   ├── domains/            # Domain expertise
│   ├── workflows/          # Process documentation
│   ├── tools/              # Tool-specific guides
│   ├── templates/          # Agent templates (NEW!)
│   └── common/             # Shared knowledge
├── personal/               # Personal customizations (NEW!)
├── agents/                 # Agent configurations
├── registry/               # MCP server registry (NEW!)
└── backups/                # Automatic backups (NEW!)
```

### Agent Templates
Pre-built templates for common roles:
- **Software Engineer**: Development-focused with Git, filesystem tools
- **Software Architect**: Architecture and design patterns
- **System Administrator**: Infrastructure and operations
- **Daily Assistant**: General productivity and task management
- **Product Owner**: Product management and planning

## 🔧 Advanced Usage

### Library Synchronization
```bash
# Check for conflicts before syncing
ai-config library sync --dry-run

# Interactive conflict resolution
ai-config library sync

# Show detailed differences
ai-config library diff --file specific-file.md
```

### Local File Integration
```bash
# Add project-specific files to agents
ai-config files add-files my-agent --pattern "./docs/**/*.md"
ai-config files add-files my-agent --pattern "./rules/*.txt"

# Enable file watching for auto-updates
ai-config files watch-files my-agent --enable

# Scan for files without adding
ai-config files scan-files my-agent --pattern "**/*.py" --base-path ./src
```

### MCP Server Management
```bash
# Create sample registry for testing
ai-config mcp create-sample

# Browse servers by category
ai-config mcp browse --category development

# Search for specific functionality
ai-config mcp search database
ai-config mcp search "file system"

# Install servers for enhanced capabilities
ai-config mcp install git
ai-config mcp install filesystem
```

### Template Usage
Templates are stored in `library/templates/` and can be:
- Used during agent creation via wizards
- Customized in your personal library
- Shared through library synchronization
- Created by copying existing role files

## 🛠️ Development

### Running Tests
```bash
# Run all tests
pytest

# Run Phase 2 specific tests
pytest tests/test_phase2_*.py -v

# Run with coverage
pytest --cov=ai_configurator
```

### Project Structure
```
ai_configurator/
├── models/                 # Pydantic data models
│   ├── sync_models.py     # Library sync models (NEW!)
│   ├── file_models.py     # File management models (NEW!)
│   ├── registry_models.py # MCP registry models (NEW!)
│   └── wizard_models.py   # Wizard models (NEW!)
├── services/              # Business logic services
│   ├── sync_service.py    # Library synchronization (NEW!)
│   ├── file_service.py    # File management (NEW!)
│   ├── registry_service.py # MCP registry (NEW!)
│   └── wizard_service.py  # Interactive wizards (NEW!)
├── cli/                   # CLI command modules (NEW!)
│   ├── sync_commands.py   # Library sync commands
│   ├── file_commands.py   # File management commands
│   ├── registry_commands.py # MCP registry commands
│   └── wizard_commands.py # Wizard commands
└── cli_enhanced.py        # Main CLI interface
```

## 🔄 Migration from Phase 1

Phase 2 maintains full backward compatibility with Phase 1 configurations. Your existing agents and MCP servers will continue to work without changes.

New features are additive and optional:
- Library sync is available but not required
- Local file integration is opt-in per agent
- MCP registry enhances but doesn't replace existing MCP management
- Wizards provide alternative setup methods alongside existing commands

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline help (`ai-config --help`)
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas

## 🎉 What's New

### 🚀 **Phase 3: Production Ready** (Latest)
- Git-based library management with remote repositories
- Performance optimization with intelligent caching (3.3x speedup)
- Production configuration management with environment support
- Comprehensive logging and error handling
- Health monitoring and system diagnostics

### ✅ **Phase 2: Advanced Library Management**
- Conflict-aware library sync with interactive resolution
- Local file integration with glob patterns and file watching
- MCP server registry with discovery and installation
- Interactive wizards and pre-built templates

### 🏗️ **Phase 1: Foundation**
- Tool-agnostic knowledge library system
- Multi-tool agent support (Q CLI, Claude, ChatGPT)
- Role-based organization and MCP integration

---

**AI Configurator v4.0.0** - Production-ready tool-agnostic knowledge library manager


# Navigate with arrow keys, Enter to select, Esc to go back
```

### Create Your First Agent

1. **Launch TUI**: `ai-config`
2. **Select "Agent Management"**
3. **Press `n` to create new agent**
4. **Press `e` to edit the agent**
5. **Select resources** with Space key
6. **Select MCP servers** with Space key  
7. **Press Ctrl+S to save**
8. **Agent auto-exports to Q CLI!**

## 📖 Usage Guide

### Agent Management

**Keyboard Shortcuts:**
- `n` - Create new agent
- `e` - Edit selected agent
- `m` - Rename agent
- `d` - Delete agent
- `x` - Export to Q CLI
- `r` - Refresh list

**Agent Editor:**
- `Space` - Toggle selection (checkbox)
- `Tab` - Switch between tables
- `↑/↓` - Navigate items
- `Ctrl+S` - Save changes
- `Esc` - Cancel

### Library Management

**Keyboard Shortcuts:**
- `n` - Create new file
- `e` - Edit file (personal files only)
- `c` - Clone file (base → personal)
- `r` - Refresh list

### MCP Server Management

**Keyboard Shortcuts:**
- `a` - Add new server
- `e` - Edit server config
- `d` - Delete server
- `s` - Sync registry
- `r` - Refresh list

**Supported JSON Formats:**
```json
// Format 1: mcpServers wrapper
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["@package/server"]
    }
  }
}

// Format 2: Direct entry (auto-wrapped)
"server-name": {
  "command": "npx",
  "args": ["@package/server"]
}
```

## 🗂️ Directory Structure

```
~/.config/ai-configurator/
├── agents/                    # Agent configurations
├── library/
│   ├── base/                  # Shared templates
│   └── personal/              # Your custom files
├── registry/
│   └── servers/               # MCP server configs
└── logs/
    └── tui.log               # Application logs

~/.aws/amazonq/cli-agents/     # Q CLI agents (auto-synced)
```

## 🔧 CLI Commands

```bash
# Agent commands
ai-config agent list
ai-config agent create my-agent
ai-config agent export my-agent

# Library commands
ai-config library list

# MCP commands
ai-config mcp list

# System commands
ai-config status
```

## 🐛 Troubleshooting

### Agent not appearing in Q CLI
```bash
# Check if exported
ls ~/.aws/amazonq/cli-agents/

# Manual export
ai-config agent export my-agent
```

### Editor not opening
```bash
# Set your preferred editor
export EDITOR=vim  # or kate, nano, etc.
```

## 📚 Documentation

- [TUI Guide](docs/TUI_GUIDE.md)
- [Agent Editor Guide](docs/AGENT_EDITOR_GUIDE.md)
- [Keyboard Shortcuts](docs/KEYBOARD_SHORTCUTS.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
