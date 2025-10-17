"""
MCP Server domain model and configurations.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .value_objects import HealthStatus


class MCPServerConfig(BaseModel):
    """MCP server configuration for agents."""
    command: str = Field(..., description="Command to execute the server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")
    timeout: int = Field(default=120000, description="Request timeout in milliseconds")
    disabled: bool = Field(default=False, description="Whether server is disabled")
    auto_approve: List[str] = Field(default_factory=list, description="Auto-approved tools", alias="autoApprove")
    
    class Config:
        populate_by_name = True


class MCPServer(BaseModel):
    """MCP Server domain entity."""
    name: str = Field(..., description="Unique server identifier")
    description: str = Field(default="", description="Server description")
    command: str = Field(..., description="Execution command")
    args: List[str] = Field(default_factory=list)
    env: Optional[Dict[str, str]] = Field(default=None)
    timeout: int = Field(default=120000, ge=1)
    category: str = Field(default="general", description="Server functionality category")
    status: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    version: Optional[str] = Field(default=None)
    
    def to_config(self) -> MCPServerConfig:
        """Convert to configuration format."""
        return MCPServerConfig(
            command=self.command,
            args=self.args,
            env=self.env,
            timeout=self.timeout,
            disabled=self.status == HealthStatus.ERROR
        )
    
    def validate_config(self) -> bool:
        """Validate server configuration."""
        if not self.command.strip():
            self.status = HealthStatus.ERROR
            return False
        
        if self.timeout <= 0:
            self.status = HealthStatus.ERROR
            return False
        
        self.status = HealthStatus.HEALTHY
        return True
