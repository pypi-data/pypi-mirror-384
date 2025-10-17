"""Deploy agent operation for Canvas CLI."""

from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils.config import ConfigManager
from ..utils.exceptions import APIError, AuthenticationError
from ..services.api_client import APIClient
from ..utils.helpers import _resolve_project_id, require_canvas_workspace, require_authentication

console = Console()


def deploy_agent_operation(target_project: str, agent: str, profile: Optional[str]) -> None:
    """Deploy an agent to the Canvas platform."""
    try:
        # Validate we're in a Canvas workspace
        require_canvas_workspace()
        
        # Validate authentication
        require_authentication(profile)
        
        # Get profile and API client
        config_manager = ConfigManager()
        user_profile = config_manager.get_profile(profile)
        
        if not user_profile:
            console.print("[red]No authentication profile found. Run 'canvas login' first.[/red]")
            raise click.Abort()
        
        api_client = APIClient(user_profile)
        
        # Resolve target project ID
        if not target_project:
            target_project = config_manager.get_default_project()
            
        target_project_id = _resolve_project_id(target_project)
        if not target_project_id:
            console.print(f"[red]Project '{target_project}' not found. Run 'canvas add project {target_project}' first.[/red]")
            raise click.Abort()
        
        # Resolve agent ID from short name or use as ID directly
        try:
            # First try to get agent by short name
            agent_obj = api_client.get_agent_by_short_name(target_project_id, agent)
            agent_id = agent_obj.get("id")
            agent_name = agent_obj.get("agentName", agent)
        except APIError:
            # If not found by short name, try using agent as ID directly
            try:
                agent_obj = api_client.get_agent(target_project_id, agent)
                agent_id = agent_obj.get("id")
                agent_name = agent_obj.get("agentName", agent)
            except APIError:
                console.print(f"[red]Agent '{agent}' not found in project '{target_project}'.[/red]")
                console.print("[blue]Use 'canvas list agents' to see available agents.[/blue]")
                raise click.Abort()
        
        console.print(f"[blue]Deploying agent '{agent_name}' in project '{target_project}'...[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            deploy_task = progress.add_task("Deploying agent...", total=None)
            
            # Deploy the agent
            result = api_client.deploy_agent(target_project_id, agent_id)
            
            progress.update(deploy_task, description="Deployment complete")
        
        console.print(f"\n[green]✓[/green] Agent '{agent_name}' deployed successfully!")
        
        # Show deployment details if available
        if result:
            if "deploymentUrl" in result:
                console.print(f"[blue]Deployment URL:[/blue] {result['deploymentUrl']}")
            if "status" in result:
                console.print(f"[blue]Status:[/blue] {result['status']}")
        
    except AuthenticationError as e:
        console.print(f"[red]Authentication Error:[/red] {e}")
        console.print("[blue]Run 'canvas login' to authenticate.[/blue]")
        raise click.Abort()
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
