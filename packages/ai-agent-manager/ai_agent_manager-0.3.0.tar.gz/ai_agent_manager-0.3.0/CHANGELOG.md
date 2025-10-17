# Changelog

All notable changes to AI Agent Manager will be documented in this file.

## [0.2.0] - 2025-10-08

### 🎉 Q CLI Agent Import Feature

Import existing Q CLI agents into AI Agent Manager with smart merge and resource handling.

### ✨ Added

**Q CLI Import:**
- Import agents from `~/.aws/amazonq/cli-agents/` with `i` key in Agent Management
- Multi-select agents to import with Space key
- Smart merge for agents that exist in both locations
  - Combines resources and MCP servers (union)
  - Keeps local description/prompt when different
  - Shows merge summary
- Resource path resolution with user prompts
  - "Copy to library" or "Keep absolute path" per file
  - "Apply to All" option for bulk operations
  - Handles `file://` URIs from Q CLI
- MCP server extraction to registry
  - Auto-numbering for duplicate names (e.g., `fetch-2.json`)
  - Preserves full server configuration
- Import selection screen shows:
  - New agents (green)
  - Existing agents that will be merged (yellow)
  - Selection count
- Detailed error messages in notifications

### 🐛 Fixed

- Handle `file://` URI prefix in Q CLI resource paths
- Expand `~` in file paths
- Skip non-existent resource files gracefully
- Use correct Pydantic models (ResourcePath, MCPServerConfig)
- Add required `source` field to ResourcePath objects
- Use correct filename format: `{name}_{tool_type}.json`
- Improved error logging and user feedback

### 📝 Notes

This implements Phase 1 of the Q CLI sync feature. Import is one-way (Q CLI → AI Agent Manager). Future versions may add bidirectional sync.

---

## [0.1.3] - 2025-10-08

### 🐛 Fixed

- Copy default MCP servers to `servers/` subdirectory where MCP manager expects them

---

## [0.1.2] - 2025-10-08

### ✨ Added

- 4 default MCP servers: fetch, browser, filesystem, github
- Automatically copied to user's registry on first run

---

## [0.1.1] - 2025-10-08

### 🐛 Fixed

- Include `ai_configurator` module in wheel package
- Fix package build configuration

---

## [0.1.0] - 2025-10-08

### 🎉 Initial Beta Release

First public release of AI Agent Manager - a terminal UI for managing AI agents across multiple tools.

### ✨ Features

**TUI (Terminal User Interface):**
- Visual menu-driven interface with keyboard navigation
- Dual-pane agent editor with multi-select (Space key)
- Real-time agent configuration preview
- Integrated help and keyboard shortcuts
- Error logging to `~/.config/ai-configurator/logs/tui.log`

**Agent Management:**
- Create, edit, rename, delete agents
- Visual resource selection with checkboxes
- Visual MCP server selection with checkboxes
- Auto-export to Q CLI (`~/.aws/amazonq/cli-agents/`)
- Manual export with `x` key
- Agent validation

**Library Management:**
- Base library with 5 default templates (daily-assistant, software-engineer, system-administrator, product-owner, software-architect)
- Personal library for custom files
- Clone base files to personal for editing
- Create new files with templates
- Visual separation of base vs personal files

**MCP Server Management:**
- Add servers by pasting JSON configs
- Flexible JSON parsing (handles multiple formats)
- Edit server configurations
- Delete servers
- Browse MCP registry

**Package:**
- Published as `ai-agent-manager` on PyPI
- CLI commands: `ai-agent-manager` and `ai-config`
- Bundled templates included in package
- GitHub Actions CI/CD pipeline

### 📝 Notes

This is a beta release. Feedback and bug reports welcome at https://github.com/jschwellach/ai-configurator/issues

---

## [4.0.0] - 2025-10-07 (Internal)

### 🎉 Major Release - Complete Redesign

AI Configurator v4.0 was a complete rewrite focused on Amazon Q CLI integration with a visual TUI interface.

### ✨ Added

**TUI (Terminal User Interface):**
- Visual menu-driven interface with keyboard navigation
- Dual-pane agent editor with multi-select (Space key)
- Real-time agent configuration preview
- Integrated help and keyboard shortcuts
- Error logging to `~/.config/ai-configurator/logs/tui.log`

**Agent Management:**
- Create, edit, rename, delete agents
- Visual resource selection with checkboxes
- Visual MCP server selection with checkboxes
- Auto-export to Q CLI (`~/.aws/amazonq/cli-agents/`)
- Manual export with `x` key
- Agent validation

**Library Management:**
- Base library (shared templates)
- Personal library (custom files)
- Clone base files to personal for customization
- Edit files in your preferred editor
- Create new markdown files
- Visual separation between base and personal files

**MCP Server Management:**
- Add servers by pasting JSON configs
- Flexible JSON parsing (handles multiple formats)
- Edit server configurations
- Delete servers
- Sync with MCP registry
- Auto-strip trailing commas from pasted JSON

**CLI Commands:**
- Simplified command structure: `ai-config <resource> <action>`
- Agent commands: list, create, export
- Library commands: list
- MCP commands: list
- System commands: status, health

### 🔄 Changed

- **Breaking**: Complete rewrite of internal architecture
- **Breaking**: New configuration directory structure
- **Breaking**: Agents now stored in `~/.config/ai-configurator/agents/`
- **Breaking**: Library split into `base/` and `personal/` directories
- **Breaking**: MCP servers in `~/.config/ai-configurator/registry/servers/`

### 🗑️ Removed

- Old CLI interface (replaced with simplified version)
- Profile system (replaced with agents)
- Hook system (may return in future version)
- Context manager (replaced with library)

### 🐛 Fixed

- Library file indexing now uses relative paths
- MCP server JSON parsing handles multiple formats
- Agent editor properly handles immutable Pydantic models
- Cursor position preserved during table refresh
- Editor selection (kate, vim, vi) with proper blocking

### 📚 Documentation

- Complete README rewrite with quick start guide
- TUI Guide with keyboard shortcuts
- Agent Editor Guide with dual-pane usage
- Migration Guide from v3.x

### 🔧 Technical

- Built with Textual TUI framework
- Pydantic models for data validation
- Async-safe event handling
- Comprehensive error logging
- Type hints throughout codebase

## [3.x] - Previous Versions

See git history for v3.x changes.
