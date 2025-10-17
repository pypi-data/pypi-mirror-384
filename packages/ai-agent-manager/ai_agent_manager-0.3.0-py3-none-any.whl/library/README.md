# AI Configurator Knowledge Library

This is a tool-agnostic knowledge library that can be consumed by any AI tool or system. The library contains pure knowledge in markdown format, organized by category.

## Structure

- **`common/`** - Organizational knowledge and policies applied across all roles
- **`roles/`** - Role-specific knowledge folders with main files and additional configurations
- **`domains/`** - Domain-specific expertise and best practices
- **`tools/`** - Tool-specific knowledge and usage patterns
- **`workflows/`** - Process and workflow documentation

## Usage

### Direct Consumption
Any AI tool can directly read markdown files from this library:
- Point Claude Projects to a role folder: `library/roles/product-owner/`
- Use ChatGPT custom instructions with content from role files
- Reference specific domain knowledge: `library/domains/aws-best-practices.md`

### AI Configurator Tool
Use the AI Configurator tool to create tool-specific agents:
```bash
ai-config create-agent --name product-owner --rules roles/product-owner/ common/policies.md --tool q-cli
ai-config update-agent --name product-owner  # Interactive configuration
```

## Role Folders

Each role has its own folder containing:
- **Main role file** (e.g., `product-owner.md`) - Core knowledge for the role
- **Additional files** - Supplementary configurations, patterns, or user-specific additions

## Version

Library Version: 2.0.0 (Tool-Agnostic Architecture)

## License

MIT License - Knowledge can be freely used and adapted.
