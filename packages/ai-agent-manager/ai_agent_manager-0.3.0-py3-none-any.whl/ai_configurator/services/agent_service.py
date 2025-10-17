"""
Agent service for managing AI agent lifecycle and operations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models import Agent, AgentConfig, ToolType, HealthStatus


class AgentService:
    """Service for agent lifecycle management."""
    
    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self.agents_dir.mkdir(parents=True, exist_ok=True)
    
    def create_agent(self, name: str, tool_type: ToolType, description: str = "") -> Optional[Agent]:
        """Create a new agent."""
        if self.agent_exists(name, tool_type):
            return None
        
        config = AgentConfig(
            name=name,
            description=description,
            tool_type=tool_type
        )
        
        agent = Agent(config=config)
        
        if agent.validate() and self._save_agent(agent):
            return agent
        return None
    
    def load_agent(self, name: str, tool_type: ToolType) -> Optional[Agent]:
        """Load an existing agent."""
        agent_file = self._get_agent_file(name, tool_type)
        if not agent_file.exists():
            return None
        
        try:
            data = json.loads(agent_file.read_text())
            config = AgentConfig(**data)
            agent = Agent(config=config)
            agent.validate()  # Update health status
            return agent
        except Exception:
            return None
    
    def update_agent(self, agent: Agent) -> bool:
        """Update an existing agent."""
        if not agent.validate():
            return False
        
        agent.config.updated_at = datetime.now()
        return self._save_agent(agent)
    
    def delete_agent(self, name: str, tool_type: ToolType) -> bool:
        """Delete an agent."""
        agent_file = self._get_agent_file(name, tool_type)
        if agent_file.exists():
            try:
                agent_file.unlink()
                return True
            except Exception:
                pass
        return False
    
    def list_agents(self, tool_type: Optional[ToolType] = None) -> List[Agent]:
        """List all agents, optionally filtered by tool type."""
        agents = []
        
        for agent_file in self.agents_dir.glob("*.json"):
            try:
                data = json.loads(agent_file.read_text())
                config = AgentConfig(**data)
                
                if tool_type is None or config.tool_type == tool_type:
                    agent = Agent(config=config)
                    agent.validate()  # Update health status
                    agents.append(agent)
            except Exception:
                continue
        
        return sorted(agents, key=lambda a: a.config.name)
    
    def agent_exists(self, name: str, tool_type: ToolType) -> bool:
        """Check if an agent exists."""
        return self._get_agent_file(name, tool_type).exists()
    
    def export_for_tool(self, agent: Agent) -> Dict:
        """Export agent configuration for its target tool."""
        if agent.tool_type == ToolType.Q_CLI:
            return agent.to_q_cli_format()
        elif agent.tool_type == ToolType.CLAUDE:
            return self._to_claude_format(agent)
        elif agent.tool_type == ToolType.CHATGPT:
            return self._to_chatgpt_format(agent)
        else:
            return agent.config.dict()
    
    def export_to_q_cli(self, agent: Agent) -> bool:
        """Export agent to Q CLI agents directory."""
        if agent.tool_type != ToolType.Q_CLI:
            return False
        
        try:
            # Q CLI agents directory
            q_cli_dir = Path.home() / ".aws" / "amazonq" / "cli-agents"
            q_cli_dir.mkdir(parents=True, exist_ok=True)
            
            # Export agent config
            config = agent.to_q_cli_format()
            agent_file = q_cli_dir / f"{agent.name}.json"
            
            agent_file.write_text(json.dumps(config, indent=2, default=str))
            return True
        except Exception:
            return False
    
    def _save_agent(self, agent: Agent) -> bool:
        """Save agent to file."""
        agent_file = self._get_agent_file(agent.name, agent.tool_type)
        
        try:
            data = agent.config.dict()
            agent_file.write_text(json.dumps(data, indent=2, default=str))
            return True
        except Exception:
            return False
    
    def _get_agent_file(self, name: str, tool_type: ToolType) -> Path:
        """Get the file path for an agent."""
        filename = f"{name}_{tool_type.value}.json"
        return self.agents_dir / filename
    
    def _to_claude_format(self, agent: Agent) -> Dict:
        """Export agent for Claude Projects (placeholder)."""
        return {
            "name": agent.name,
            "description": agent.config.description,
            "knowledge_files": [r.path for r in agent.config.resources],
            "instructions": f"You are {agent.name}. {agent.config.description}"
        }
    
    def _to_chatgpt_format(self, agent: Agent) -> Dict:
        """Export agent for ChatGPT (placeholder)."""
        return {
            "name": agent.name,
            "description": agent.config.description,
            "custom_instructions": f"You are {agent.name}. {agent.config.description}",
            "knowledge_base": [r.path for r in agent.config.resources]
        }
