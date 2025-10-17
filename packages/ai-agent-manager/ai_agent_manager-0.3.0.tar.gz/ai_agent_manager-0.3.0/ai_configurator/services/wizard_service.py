"""
Wizard service for interactive setup processes.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel

from ..models.wizard_models import Wizard, WizardStep, Template, TemplateLibrary, WizardResult
from ..models.value_objects import ToolType
from ..services.agent_service import AgentService
from ..services.registry_service import RegistryService


class WizardService:
    """Service for managing interactive wizards."""
    
    def __init__(self, library_service, console: Optional[Console] = None):
        self.console = console or Console()
        self.library_service = library_service
    
    def create_agent_wizard(self) -> Wizard:
        """Create wizard for agent setup."""
        steps = [
            WizardStep(
                step_id="agent_name",
                title="Agent Name",
                description="Choose a name for your AI agent",
                prompt="Enter agent name",
                input_type="text",
                validation_pattern=r"^[a-zA-Z0-9_-]+$"
            ),
            WizardStep(
                step_id="tool_type",
                title="Target Tool",
                description="Select the AI tool this agent will work with",
                prompt="Select target tool",
                input_type="choice",
                choices=[tool.value for tool in ToolType],
                default_value=ToolType.Q_CLI.value
            ),
            WizardStep(
                step_id="description",
                title="Description",
                description="Provide a description for your agent",
                prompt="Enter agent description",
                input_type="text",
                required=False
            ),
            WizardStep(
                step_id="use_template",
                title="Use Template",
                description="Would you like to use a pre-built template?",
                prompt="Use a template?",
                input_type="confirm",
                default_value=False
            )
        ]
        
        return Wizard(
            wizard_id="agent_creation",
            title="Create New Agent",
            description="Set up a new AI agent with guided configuration",
            steps=steps
        )
    
    def create_mcp_wizard(self, agent_name: str) -> Wizard:
        """Create wizard for MCP server setup."""
        steps = [
            WizardStep(
                step_id="browse_servers",
                title="Browse Servers",
                description="Would you like to browse available MCP servers?",
                prompt="Browse MCP servers?",
                input_type="confirm",
                default_value=True
            ),
            WizardStep(
                step_id="server_selection",
                title="Server Selection",
                description="Select MCP servers to install",
                prompt="Select servers (comma-separated)",
                input_type="text",
                required=False
            ),
            WizardStep(
                step_id="auto_install",
                title="Auto Install",
                description="Automatically install selected servers?",
                prompt="Install servers automatically?",
                input_type="confirm",
                default_value=True
            )
        ]
        
        return Wizard(
            wizard_id="mcp_setup",
            title=f"MCP Setup for {agent_name}",
            description="Configure MCP servers for your agent",
            steps=steps
        )
    
    def run_wizard(self, wizard: Wizard) -> WizardResult:
        """Run an interactive wizard."""
        self.console.print(Panel(
            f"[bold]{wizard.title}[/bold]\n{wizard.description}",
            title="🧙 Setup Wizard",
            border_style="blue"
        ))
        
        while not wizard.is_complete():
            step = wizard.get_current_step()
            if not step:
                break
            
            self.console.print(f"\n📋 Step {wizard.current_step + 1}/{len(wizard.steps)}: [bold]{step.title}[/bold]")
            self.console.print(f"   {step.description}")
            
            # Get user input based on step type
            value = self._get_step_input(step)
            
            if value is None:  # User cancelled
                break
            
            # Add response and continue
            if not wizard.add_response(step.step_id, value):
                self.console.print("❌ Invalid input, please try again")
                continue
        
        result = wizard.get_result()
        
        if result.completed:
            self.console.print("\n✅ Wizard completed successfully!")
        else:
            self.console.print("\n⚠️  Wizard was cancelled or incomplete")
        
        return result
    
    def _get_step_input(self, step: WizardStep) -> Any:
        """Get user input for a wizard step."""
        try:
            if step.input_type == "text":
                return Prompt.ask(
                    step.prompt,
                    default=step.default_value if step.default_value else None
                )
            
            elif step.input_type == "choice":
                # Display choices
                table = Table(title="Available Options")
                table.add_column("Option", style="cyan")
                table.add_column("Value", style="green")
                
                for i, choice in enumerate(step.choices, 1):
                    table.add_row(str(i), choice)
                
                self.console.print(table)
                
                while True:
                    try:
                        choice_num = IntPrompt.ask(
                            f"{step.prompt} (1-{len(step.choices)})",
                            default=1 if step.default_value is None else step.choices.index(step.default_value) + 1
                        )
                        if 1 <= choice_num <= len(step.choices):
                            return step.choices[choice_num - 1]
                        else:
                            self.console.print(f"Please enter a number between 1 and {len(step.choices)}")
                    except ValueError:
                        self.console.print("Please enter a valid number")
            
            elif step.input_type == "confirm":
                return Confirm.ask(step.prompt, default=step.default_value)
            
            elif step.input_type == "multiselect":
                # Display choices with numbers
                table = Table(title="Available Options (select multiple)")
                table.add_column("Number", style="cyan")
                table.add_column("Option", style="green")
                
                for i, choice in enumerate(step.choices, 1):
                    table.add_row(str(i), choice)
                
                self.console.print(table)
                
                selections = Prompt.ask(
                    f"{step.prompt} (comma-separated numbers)",
                    default=""
                )
                
                if not selections.strip():
                    return []
                
                try:
                    indices = [int(x.strip()) - 1 for x in selections.split(',')]
                    return [step.choices[i] for i in indices if 0 <= i < len(step.choices)]
                except (ValueError, IndexError):
                    self.console.print("Invalid selection, please try again")
                    return self._get_step_input(step)
            
            return None
            
        except KeyboardInterrupt:
            return None
    
    def run_agent_creation_wizard(self, agent_service: AgentService) -> Optional[str]:
        """Run the complete agent creation wizard."""
        wizard = self.create_agent_wizard()
        result = self.run_wizard(wizard)
        
        if not result.completed:
            return None
        
        # Extract responses
        agent_name = result.get_response("agent_name")
        tool_type = ToolType(result.get_response("tool_type"))
        description = result.get_response("description", "")
        use_template = result.get_response("use_template", False)
        
        # Handle template selection
        template_resources = []
        if use_template:
            template_file = self._select_template(tool_type)
            if template_file:
                self.console.print(f"📄 Using template: {template_file}")
                # Add template as a resource
                from ..models.value_objects import ResourcePath, LibrarySource
                template_resources.append(ResourcePath(
                    path=template_file,
                    source=LibrarySource.BASE
                ))
        
        # Create agent
        agent = agent_service.create_agent(agent_name, tool_type, description)
        
        # Add template resources to agent
        if agent and template_resources:
            for resource in template_resources:
                agent.add_resource(resource)
            # Save updated agent
            agent_service.update_agent(agent)
        
        if agent:
            resource_count = len(agent.config.resources)
            self.console.print(f"✅ Agent '{agent_name}' created successfully!")
            if resource_count > 0:
                self.console.print(f"📚 Added {resource_count} template resource(s)")
            return agent_name
        else:
            self.console.print(f"❌ Failed to create agent '{agent_name}'")
            return None
    
    def run_mcp_setup_wizard(self, agent_name: str, registry_service: RegistryService) -> bool:
        """Run MCP server setup wizard."""
        # Simple approach: show servers and ask for selection
        self.console.print(f"🧙 [bold]MCP Setup for {agent_name}[/bold]")
        
        # Show available servers
        servers = registry_service.search_servers("", None, 10)
        
        if not servers:
            self.console.print("No MCP servers available in registry")
            self.console.print("💡 Use 'ai-config mcp create-sample' to create sample servers")
            return False
        
        table = Table(title="Available MCP Servers")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Category", style="green")
        
        for server in servers:
            table.add_row(
                server.name,
                server.description[:50] + "..." if len(server.description) > 50 else server.description,
                server.category
            )
        
        self.console.print(table)
        
        # Ask for server selection
        from rich.prompt import Prompt, Confirm
        server_selection = Prompt.ask("Select servers (comma-separated, or 'none' to skip)", default="none")
        
        if server_selection and server_selection.lower() != "none":
            auto_install = Confirm.ask("Install servers automatically?", default=True)
            
            if auto_install:
                server_names = [name.strip() for name in server_selection.split(',')]
                
                for server_name in server_names:
                    server = next((s for s in servers if s.name == server_name), None)
                    if server:
                        self.console.print(f"📦 Installing {server_name}...")
                        success = registry_service.install_server(server_name)
                        if success:
                            self.console.print(f"✅ {server_name} installed successfully")
                        else:
                            self.console.print(f"❌ Failed to install {server_name}")
                    else:
                        self.console.print(f"⚠️  Server '{server_name}' not found")
        
        return True
    
    def _select_template(self, tool_type: ToolType) -> Optional[str]:
        """Interactive template selection from library."""
        # Get template files from library directory
        library = self.library_service.create_library()
        template_dir = library.base_path / "templates"
        
        if not template_dir.exists():
            self.console.print("No templates directory found")
            return None
        
        # Find template files for this tool type
        template_files = []
        for template_file in template_dir.glob("*.md"):
            if tool_type.value in template_file.name:
                template_files.append(str(template_file.relative_to(library.base_path)))
        
        if not template_files:
            self.console.print("No templates available for this tool type")
            return None
        
        table = Table(title=f"Templates for {tool_type.value}")
        table.add_column("Number", style="cyan")
        table.add_column("Template", style="green")
        
        for i, template_file in enumerate(template_files, 1):
            template_name = Path(template_file).stem.replace(f"-{tool_type.value}", "").replace("-", " ").title()
            table.add_row(str(i), template_name)
        
        self.console.print(table)
        
        try:
            choice = IntPrompt.ask(f"Select template (1-{len(template_files)}, 0 to skip)", default=0)
            if 1 <= choice <= len(template_files):
                return template_files[choice - 1]
        except (ValueError, KeyboardInterrupt):
            pass
        
        return None
