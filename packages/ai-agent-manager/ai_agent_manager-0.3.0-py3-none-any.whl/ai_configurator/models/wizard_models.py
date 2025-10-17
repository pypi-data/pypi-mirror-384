"""
Wizard models for interactive setup processes.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from .value_objects import ToolType


class WizardStep(BaseModel):
    """A single step in a wizard process."""
    step_id: str = Field(..., description="Unique step identifier")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    prompt: str = Field(..., description="User prompt")
    input_type: str = Field(default="text", description="Input type: text, choice, confirm, multiselect")
    choices: List[str] = Field(default_factory=list, description="Available choices for choice/multiselect")
    default_value: Optional[Union[str, bool, List[str]]] = Field(default=None, description="Default value")
    required: bool = Field(default=True, description="Whether input is required")
    validation_pattern: Optional[str] = Field(default=None, description="Regex pattern for validation")
    
    def validate_input(self, value: Any) -> bool:
        """Validate user input for this step."""
        if self.required and not value:
            return False
        
        if self.input_type == "choice" and value not in self.choices:
            return False
        
        if self.input_type == "multiselect":
            if not isinstance(value, list):
                return False
            return all(choice in self.choices for choice in value)
        
        if self.validation_pattern and isinstance(value, str):
            import re
            return bool(re.match(self.validation_pattern, value))
        
        return True


class WizardResult(BaseModel):
    """Result of a completed wizard."""
    wizard_id: str = Field(..., description="Wizard identifier")
    completed: bool = Field(..., description="Whether wizard was completed")
    responses: Dict[str, Any] = Field(default_factory=dict, description="User responses by step_id")
    completion_time: datetime = Field(default_factory=datetime.now, description="When wizard was completed")
    
    def get_response(self, step_id: str, default: Any = None) -> Any:
        """Get response for a specific step."""
        return self.responses.get(step_id, default)


class Wizard(BaseModel):
    """Interactive wizard for setup processes."""
    wizard_id: str = Field(..., description="Unique wizard identifier")
    title: str = Field(..., description="Wizard title")
    description: str = Field(..., description="Wizard description")
    steps: List[WizardStep] = Field(..., description="Wizard steps")
    current_step: int = Field(default=0, description="Current step index")
    responses: Dict[str, Any] = Field(default_factory=dict, description="Collected responses")
    
    def get_current_step(self) -> Optional[WizardStep]:
        """Get the current step."""
        if 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
    
    def add_response(self, step_id: str, value: Any) -> bool:
        """Add a response and advance to next step."""
        step = self.get_current_step()
        if not step or step.step_id != step_id:
            return False
        
        if not step.validate_input(value):
            return False
        
        self.responses[step_id] = value
        self.current_step += 1
        return True
    
    def is_complete(self) -> bool:
        """Check if wizard is complete."""
        return self.current_step >= len(self.steps)
    
    def get_result(self) -> WizardResult:
        """Get wizard result."""
        return WizardResult(
            wizard_id=self.wizard_id,
            completed=self.is_complete(),
            responses=self.responses.copy()
        )


class Template(BaseModel):
    """Configuration template for quick setup."""
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: str = Field(default="general", description="Template category")
    tool_type: ToolType = Field(..., description="Target tool type")
    
    # Template content
    agent_config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration template")
    resources: List[str] = Field(default_factory=list, description="Default resources to include")
    mcp_servers: List[str] = Field(default_factory=list, description="Default MCP servers")
    
    # Customization
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Template parameters")
    customizable_fields: List[str] = Field(default_factory=list, description="Fields that can be customized")
    
    # Metadata
    author: str = Field(default="", description="Template author")
    version: str = Field(default="1.0.0", description="Template version")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    def apply_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply parameters to template and return configured agent config."""
        config = self.agent_config.copy()
        
        # Simple parameter substitution
        for key, value in parameters.items():
            if key in self.customizable_fields:
                # Replace placeholders in config
                config = self._replace_placeholders(config, {f"{{{key}}}": value})
        
        return config
    
    def _replace_placeholders(self, obj: Any, replacements: Dict[str, Any]) -> Any:
        """Recursively replace placeholders in configuration."""
        if isinstance(obj, dict):
            return {k: self._replace_placeholders(v, replacements) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_placeholders(item, replacements) for item in obj]
        elif isinstance(obj, str):
            result = obj
            for placeholder, value in replacements.items():
                result = result.replace(placeholder, str(value))
            return result
        else:
            return obj


class TemplateLibrary(BaseModel):
    """Collection of configuration templates."""
    templates: Dict[str, Template] = Field(default_factory=dict, description="Available templates")
    categories: Dict[str, List[str]] = Field(default_factory=dict, description="Templates by category")
    
    def add_template(self, template: Template) -> None:
        """Add a template to the library."""
        self.templates[template.template_id] = template
        
        # Update categories
        if template.category not in self.categories:
            self.categories[template.category] = []
        
        if template.template_id not in self.categories[template.category]:
            self.categories[template.category].append(template.template_id)
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def get_templates_by_category(self, category: str) -> List[Template]:
        """Get all templates in a category."""
        template_ids = self.categories.get(category, [])
        return [self.templates[tid] for tid in template_ids if tid in self.templates]
    
    def get_templates_by_tool(self, tool_type: ToolType) -> List[Template]:
        """Get templates for a specific tool type."""
        return [t for t in self.templates.values() if t.tool_type == tool_type]
    
    def search_templates(self, query: str) -> List[Template]:
        """Search templates by name or description."""
        query_lower = query.lower()
        results = []
        
        for template in self.templates.values():
            if (query_lower in template.name.lower() or 
                query_lower in template.description.lower() or
                query_lower in template.category.lower()):
                results.append(template)
        
        return results
