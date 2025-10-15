# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AgentKit CLI - Main entry point for AgentKit Starter Toolkit."""

from pathlib import Path
from typing import Optional
from agentkit.toolkit.config import get_config, CommonConfig
import logging

logging.basicConfig(level=logging.ERROR)

from agentkit.toolkit.workflows import WORKFLOW_REGISTRY, Workflow
from rich.panel import Panel
import typer
from rich.console import Console

app = typer.Typer(
    name="agentkit",
    help="AgentKit CLI - Deploy AI agents with ease",
    add_completion=False,
)

console = Console()


@app.command()
def init(
    project_name: Optional[str] = typer.Argument(None, help="Project name"),
    template: str = typer.Option("basic", help="Project template"),
    directory: Optional[Path] = typer.Option(None, help="Target directory"),
):
    """Initialize a new Agent project with templates."""
    target_dir = directory or Path.cwd()
    project_name = project_name or "my_agent"
    
    console.print(f"[bold green]Creating project: {project_name}[/bold green]")
    
    file_name = f"{project_name}.py"
    agent_file_path = target_dir / file_name
    
    if agent_file_path.exists():
        console.print(f"[yellow]File {file_name} already exists, skipping creation[/yellow]")
        return
    
    try:
        source_path = Path(__file__).parent.parent / "resources" / "samples" / "simple_app_veadk.py"
        
        with open(source_path, 'r', encoding='utf-8') as source_file:
            content = source_file.read()
        
        with open(agent_file_path, 'w', encoding='utf-8') as agent_file:
            agent_file.write(content)
        
        console.print(f"[bold green]Successfully created file: {file_name}[/bold green]")
        console.print("[bold blue]Tip: Use 'agentkit config' to configure your agent[/bold blue]")
        
    except Exception as e:
        console.print(f"[red]Failed to create file: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def config(
    interactive: bool = typer.Option(True, help="Use interactive configuration"),
    config_file: Optional[str] = typer.Option(None, help="Configuration file path")
):
    """Configure AgentKit interactively"""
    if not interactive:
        typer.echo("Non-interactive configuration mode is deprecated")
        return
    
    config = get_config(config_path=config_file)
    
    common_config = CommonConfig.interactive_create(config.get_common_config().to_dict())
    config.update_common_config(common_config)
    
    workflow_name = common_config.current_workflow
    
    if workflow_name in WORKFLOW_REGISTRY:
        workflow = WORKFLOW_REGISTRY[workflow_name]()
        workflow_config = workflow.prompt_for_config(config.get_workflow_config(workflow_name))
        config.update_workflow_config(workflow_name, workflow_config)
        
        common_config.current_workflow = workflow_name
        config.update_common_config(common_config)
    
    typer.echo("✅ Configuration completed!")


@app.command()
def build(
    config_file: Path = typer.Option("agentkit.yaml", help="Configuration file"),
    platform: str = typer.Option("auto", help="Build platform"),
    push: bool = typer.Option(True, help="Push image to registry"),
):
    """Build Docker image for the Agent."""
    console.print(f"[blue]Building image with {config_file}[/blue]")
    
    config = get_config(config_path=config_file)
    common_config = config.get_common_config()

    if not common_config.entry_point:
        console.print("[red]Entry point not configured, cannot build image[/red]")
        raise typer.Exit(1)
    
    workflow_name = common_config.current_workflow
    if workflow_name not in WORKFLOW_REGISTRY:
        console.print(f"[red]Error: Unknown workflow type '{workflow_name}'[/red]")
        raise typer.Exit(1)
    
    workflow_config = config.get_workflow_config(workflow_name)
    
    workflow = WORKFLOW_REGISTRY[workflow_name]()
    success = workflow.build(workflow_config)
    
    if not success:
        raise typer.Exit(1)


@app.command()
def deploy(
    config_file: Path = typer.Option("agentkit.yaml", help="Configuration file"),
):
    """Deploy the Agent to target environment."""
    console.print(f"[green]Deploying with {config_file}[/green]")
    
    config = get_config(config_path=config_file)
    common_config = config.get_common_config()

    if not common_config.entry_point:
        console.print("[red]Entry point not configured, cannot deploy[/red]")
        raise typer.Exit(1)
    
    workflow_name = common_config.current_workflow
    if workflow_name not in WORKFLOW_REGISTRY:
        console.print(f"[red]Error: Unknown workflow type '{workflow_name}'[/red]")
        raise typer.Exit(1)
    
    workflow_config = config.get_workflow_config(workflow_name)
    
    workflow = WORKFLOW_REGISTRY[workflow_name]()
    success = workflow.deploy(workflow_config)
    
    if not success:
        raise typer.Exit(1)


@app.command()
def launch(
    config_file: Path = typer.Option("agentkit.yaml", help="Configuration file"),
):
    """Build and deploy in one command."""
    console.print("[green]Launching agent...[/green]")
    build(config_file=config_file)
    deploy(config_file=config_file)
    


@app.command()
def invoke(
    config_file: Path = typer.Option("agentkit.yaml", help="Configuration file"),
    payload: str = typer.Argument(..., help="JSON payload to send"),
    apikey: str = typer.Option(
        None, "--apikey", "-ak", help="API key for authentication"
    ),
):
    """Send a test request to deployed Agent."""
    console.print("[cyan]Invoking agent...[/cyan]")
    
    config = get_config(config_path=config_file)
    common_config = config.get_common_config()
    
    workflow_name = common_config.current_workflow
    if workflow_name not in WORKFLOW_REGISTRY:
        console.print(f"[red]Error: Unknown workflow type '{workflow_name}'[/red]")
        raise typer.Exit(1)
    
    workflow_config = config.get_workflow_config(workflow_name)
    
    workflow: Workflow = WORKFLOW_REGISTRY[workflow_name]()
    success = workflow.invoke(workflow_config, {"payload": payload, "apikey": apikey})
    
    if not success:
        raise typer.Exit(1)



@app.command()
def status(
    config_file: Path = typer.Option("agentkit.yaml", help="Configuration file"),
):
    """Show current status of the agent runtime."""
    try:
        config = get_config(config_path=config_file)
        common_config = config.get_common_config()
        workflow_type = common_config.current_workflow

        if workflow_type not in WORKFLOW_REGISTRY:
            console.print(f"[red]Error: Unknown workflow type '{workflow_type}'[/red]")
            raise typer.Exit(1)

        workflow = WORKFLOW_REGISTRY[workflow_type]()
        workflow_config = config.get_workflow_config(workflow_type)
        status_result = workflow.status(workflow_config)

        if isinstance(status_result, dict) and status_result.get('error'):
            console.print(f"[red]Status query failed: {status_result['error']}[/red]")
            raise typer.Exit(1)

        console.print(status_result)

    except Exception as e:
        console.print(f"[red]Status query failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def destroy(
    config_file: Path = typer.Option("agentkit.yaml", help="Configuration file"),
    force: bool = typer.Option(False, help="Force destroy without confirmation"),
):
    """Destroy running Agent runtime."""
    console.print(f"[red]Destroying current workflow runtime...[/red]")
    if not force:
        typer.confirm("Are you sure you want to destroy?", abort=True)
    
    try:
        config = get_config(config_path=config_file)
        common_config = config.get_common_config()
        
        workflow_name = common_config.current_workflow
        if workflow_name not in WORKFLOW_REGISTRY:
            console.print(f"[red]Error: Unknown workflow type '{workflow_name}'[/red]")
            raise typer.Exit(1)
        
        workflow = WORKFLOW_REGISTRY[workflow_name]()
        workflow.destroy()
        
        console.print(f"[green]✅ {workflow_name} runtime destroyed successfully[/green]")
        
    except Exception as e:
        console.print(f"[red]Destruction failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def help(
    command: Optional[str] = typer.Argument(None, help="Specific command to get help for"),
):
    """Show detailed help information for AgentKit CLI commands."""
    if command:
        help_text = {
            "init": """
[bold cyan]agentkit init[/bold cyan] - Initialize a new Agent project

Usage:
    agentkit init [PROJECT_NAME] [OPTIONS]

Arguments:
    PROJECT_NAME    Name of the project (default: my-agent)

Options:
    --template TEXT     Project template to use (default: basic)
    --directory PATH    Target directory for the project
    
Examples:
    agentkit init my-agent
    agentkit init my-agent --template advanced
    agentkit init --directory ./projects
""",
            "config": """
[bold cyan]agentkit config[/bold cyan] - Interactive configuration for AgentKit

Usage:
    agentkit config [OPTIONS]

Options:
    --interactive       Use interactive configuration mode (default: True)
    --config-file PATH  Path to configuration file
    
This command guides you through configuring your AgentKit setup,
including workflow selection and API credentials.
""",
            "build": """
[bold cyan]agentkit build[/bold cyan] - Build Docker image for the Agent

Usage:
    agentkit build [OPTIONS]

Options:
    --config-file PATH  Configuration file path (default: agentkit.yaml)
    --platform TEXT     Build platform (default: auto)
    --push / --no-push  Push image to registry (default: True)
    
Requirements:
    - Entry point must be configured in agentkit.yaml
    - Valid workflow configuration
""",
            "deploy": """
[bold cyan]agentkit deploy[/bold cyan] - Deploy the Agent to target environment

Usage:
    agentkit deploy [OPTIONS]

Options:
    --config-file PATH  Configuration file path (default: agentkit.yaml)
    
This command deploys your built agent to the configured environment.
""",
            "launch": """
[bold cyan]agentkit launch[/bold cyan] - Build and deploy in one command

Usage:
    agentkit launch [OPTIONS]

Options:
    --config-file PATH  Configuration file path (default: agentkit.yaml)
    
This is a convenience command that runs build followed by deploy.
""",
            "invoke": """
[bold cyan]agentkit invoke[/bold cyan] - Send a test request to deployed Agent

Usage:
    agentkit invoke PAYLOAD [OPTIONS]

Arguments:
    PAYLOAD    JSON payload to send to the agent

Options:
    --config-file PATH  Configuration file path (default: agentkit.yaml)
    --apikey TEXT       API key for authentication
    
Example:
    agentkit invoke '{"message": "Hello, agent!"}'
""",
            "status": """
[bold cyan]agentkit status[/bold cyan] - Check Agent status

Usage:
    agentkit status [OPTIONS]

Options:
    --config-file PATH  Configuration file path (default: agentkit.yaml)
    
Displays the current status of your deployed agent.
""",
            "destroy": """
[bold cyan]agentkit destroy[/bold cyan] - Destroy running Agent runtime

Usage:
    agentkit destroy [OPTIONS]

Options:
    --config-file PATH  Configuration file path (default: agentkit.yaml)
    --force             Force destroy without confirmation
    
This command stops and removes your deployed agent runtime.
Use with caution as this will terminate your running agent.
""",
        }
        
        if command in help_text:
            console.print(Panel(help_text[command], title=f"Help: {command}", border_style="cyan"))
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("Available commands: init, config, build, deploy, launch, invoke, status, destroy, help")
    else:
        general_help = """
[bold cyan]AgentKit CLI - Deploy AI agents with ease[/bold cyan]

[bold]Available Commands:[/bold]

[cyan]Project Management:[/cyan]
  [green]init[/green]     - Initialize a new Agent project
  [green]config[/green]   - Interactive configuration for AgentKit

[cyan]Build & Deploy:[/cyan]
  [green]build[/green]    - Build Docker image for the Agent
  [green]deploy[/green]   - Deploy the Agent to target environment
  [green]launch[/green]   - Build and deploy in one command

[cyan]Runtime Management:[/cyan]
  [green]invoke[/green]   - Send a test request to deployed Agent
  [green]status[/green]   - Check Agent status
  [green]destroy[/green] - Destroy running Agent runtime

[cyan]Help:[/cyan]
  [green]help[/green]     - Show this help message or help for specific command

[bold]Usage Examples:[/bold]
  agentkit init my-agent --template basic
  agentkit config
  agentkit build
  agentkit deploy
  agentkit launch
  agentkit invoke '{"prompt": "hello world!"}'
  agentkit status
  agentkit help build

[bold]Global Options:[/bold]
  --help  Show help message and exit

For more detailed help on a specific command:
  agentkit help [COMMAND]
        """
        console.print(Panel(general_help, title="AgentKit CLI Help", border_style="cyan"))


if __name__ == "__main__":
    app()