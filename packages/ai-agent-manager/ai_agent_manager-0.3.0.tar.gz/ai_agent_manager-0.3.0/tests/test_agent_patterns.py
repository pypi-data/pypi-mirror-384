"""Test agent context patterns functionality."""

from ai_configurator.models.agent import Agent, AgentConfig
from ai_configurator.models.value_objects import ToolType


def test_agent_context_patterns():
    """Test that agents can handle multiple context patterns."""
    config = AgentConfig(
        name="test-agent",
        tool_type=ToolType.Q_CLI,
        context_patterns=["**/*.md", ".amazonq/rules/**/*.txt", "docs/**/*.py"]
    )
    
    agent = Agent(config=config)
    
    # Verify patterns are stored correctly
    assert len(agent.config.context_patterns) == 3
    assert "**/*.md" in agent.config.context_patterns
    assert ".amazonq/rules/**/*.txt" in agent.config.context_patterns
    assert "docs/**/*.py" in agent.config.context_patterns
    
    # Verify Q CLI export includes patterns
    export = agent.to_q_cli_format()
    assert "resources" in export
    
    # Context patterns should be included in resources with file:// prefix
    expected_patterns = [
        "file://**/*.md",
        "file://.amazonq/rules/**/*.txt", 
        "file://docs/**/*.py"
    ]
    
    for pattern in expected_patterns:
        assert pattern in export["resources"]


def test_empty_context_patterns():
    """Test agent with no context patterns."""
    config = AgentConfig(
        name="test-agent",
        tool_type=ToolType.Q_CLI,
        context_patterns=[]
    )
    
    agent = Agent(config=config)
    
    assert len(agent.config.context_patterns) == 0
    
    export = agent.to_q_cli_format()
    assert "resources" in export
    # Should only contain regular resources, no pattern entries
    assert len(export["resources"]) == 0


if __name__ == "__main__":
    test_agent_context_patterns()
    test_empty_context_patterns()
    print("All tests passed!")
