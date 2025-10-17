"""
Agent domain model and related configurations.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .value_objects import ToolType, ResourcePath, HealthStatus
from .mcp_server import MCPServerConfig


class AgentSettings(BaseModel):
    """Tool-specific agent settings."""
    tools: List[str] = Field(default_factory=lambda: ["*"])
    allowed_tools: List[str] = Field(default_factory=list)
    tool_aliases: Dict[str, str] = Field(default_factory=dict)
    tools_settings: Dict[str, Any] = Field(default_factory=dict)
    use_legacy_mcp_json: bool = False


class AgentConfig(BaseModel):
    """Agent configuration data."""
    name: str = Field(..., description="Unique agent identifier")
    description: str = Field(default="", description="Human-readable description")
    prompt: Optional[str] = Field(default=None, description="Custom instructions/rules (system prompt)")
    tool_type: ToolType = Field(..., description="Target AI tool")
    resources: List[ResourcePath] = Field(default_factory=list)
    context_patterns: List[str] = Field(default_factory=list, description="File patterns for additional context")
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    settings: AgentSettings = Field(default_factory=AgentSettings)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Agent(BaseModel):
    """Core Agent domain entity."""
    config: AgentConfig
    health_status: HealthStatus = HealthStatus.UNKNOWN
    validation_errors: List[str] = Field(default_factory=list)
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def tool_type(self) -> ToolType:
        return self.config.tool_type
    
    def add_resource(self, resource: ResourcePath) -> None:
        """Add a knowledge file resource."""
        if resource not in self.config.resources:
            self.config.resources.append(resource)
            self.config.updated_at = datetime.now()
    
    def configure_mcp_server(self, name: str, config: MCPServerConfig) -> None:
        """Add or update MCP server configuration."""
        self.config.mcp_servers[name] = config
        self.config.updated_at = datetime.now()
    
    def validate(self) -> bool:
        """Validate agent configuration."""
        self.validation_errors.clear()
        
        # Basic validation
        if not self.config.name.strip():
            self.validation_errors.append("Agent name cannot be empty")
        
        # Resource validation
        for resource in self.config.resources:
            if not resource.path.strip():
                self.validation_errors.append(f"Empty resource path found")
        
        # MCP server validation
        for server_name, server_config in self.config.mcp_servers.items():
            if not server_config.command.strip():
                self.validation_errors.append(f"MCP server '{server_name}' has empty command")
        
        is_valid = len(self.validation_errors) == 0
        self.health_status = HealthStatus.HEALTHY if is_valid else HealthStatus.ERROR
        return is_valid
    
    def to_q_cli_format(self) -> Dict[str, Any]:
        """Export agent configuration for Q CLI."""
        # Combine regular resources and context patterns
        all_resources = [r.to_file_uri() for r in self.config.resources]
        
        # Add context patterns with file:// prefix
        for pattern in self.config.context_patterns:
            if not pattern.startswith('file://'):
                all_resources.append(f"file://{pattern}")
            else:
                all_resources.append(pattern)
        
        return {
            "$schema": "https://raw.githubusercontent.com/aws/amazon-q-developer-cli/refs/heads/main/schemas/agent-v1.json",
            "name": self.config.name,
            "description": self.config.description or None,
            "prompt": self.config.prompt,
            "resources": all_resources,
            "tools": self.config.settings.tools,
            "allowedTools": self.config.settings.allowed_tools,
            "toolAliases": self.config.settings.tool_aliases,
            "mcpServers": {name: config.dict(by_alias=True) for name, config in self.config.mcp_servers.items()},
            "toolsSettings": self.config.settings.tools_settings,
            "useLegacyMcpJson": self.config.settings.use_legacy_mcp_json,
        }
