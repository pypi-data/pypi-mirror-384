"""List command for listing Canvas resources."""

import yaml
import traceback
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ..utils.config import ConfigManager
from ..utils.exceptions import APIError
from ..services.api_client import APIClient
from ..utils.helpers import require_canvas_workspace, require_authentication

console = Console()


@click.group(name="list")
def list_cmd() -> None:
    """List Canvas resources (projects, agents, tools, etc.)."""
    pass


@list_cmd.command()
@click.option(
    "--profile",
    help="Profile to use for authentication"
)
@click.option(
    "--local",
    is_flag=True,
    help="List projects added to local workspace instead of remote projects"
)
def projects(profile: Optional[str], local: bool) -> None:
    """List all projects (remote by default, or local with --local flag)."""
    
    try:
        # Validate we're in a Canvas workspace
        require_canvas_workspace()
        
        if local:
            # List local projects
            _list_local_projects()
            return
        
        # List remote projects (original behavior)
        # Validate authentication
        require_authentication(profile)
        
        # Get profile and create API client
        config_manager = ConfigManager()
        user_profile = config_manager.get_profile(profile)
        
        api_client = APIClient(user_profile)
        
        console.print(f"[blue]Fetching projects from {user_profile.api_base}...[/blue]")
        
        # Fetch projects
        projects_data = api_client.list_projects()
        
        if not projects_data:
            console.print("[yellow]No projects found.[/yellow]")
            return
        
        # Create table
        table = Table(title="Canvas Projects", expand=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Short Name", style="magenta", overflow="fold")
        table.add_column("Name", style="bright_white", overflow="fold")
        table.add_column("Description", style="white", overflow="fold")
        table.add_column("Created", style="dim", no_wrap=True)
        
        # Add rows
        for project in projects_data:
            # Truncate description if too long
            description = project.get("description", "")
            if len(description) > 50:
                description = description[:47] + "..."
            
            # Format createdAt timestamp
            created_at = project.get("createdAt")
            if created_at:
                if isinstance(created_at, int):
                    # Convert timestamp to readable date
                    from datetime import datetime
                    created_at_str = datetime.fromtimestamp(created_at / 1000).strftime("%Y-%m-%d")
                else:
                    # Handle string format
                    created_at_str = str(created_at)[:10]
            else:
                created_at_str = "N/A"
            
            table.add_row(
                project.get("publicId", project.get("id", "N/A")),  # Use 'id' if 'publicId' not present
                project.get("shortName", "N/A"),
                project.get("name", "N/A"),
                description,
                created_at_str
            )
        
        console.print(table)
        console.print(f"\n[blue]Total projects:[/blue] {len(projects_data)}")
        
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[yellow]Full stack trace:[/yellow]")
        console.print(traceback.format_exc())
        raise click.Abort()


@list_cmd.command()
@click.option(
    "--profile",
    help="Profile to use for authentication"
)
@click.option(
    "--project",
    help="Project short name to list agents from (uses default project if not specified)"
)
def agents(profile: Optional[str], project: Optional[str]) -> None:
    """List all agents in a project."""
    
    try:
        # Validate we're in a Canvas workspace
        require_canvas_workspace()
        
        # Validate authentication
        require_authentication(profile)
        
        # Get profile and create API client
        config_manager = ConfigManager()
        user_profile = config_manager.get_profile(profile)
        
        api_client = APIClient(user_profile)
        
        # Determine which project to use
        if project:
            target_project = project
        else:
            target_project = config_manager.get_default_project()
            if not target_project:
                console.print("[red]No default project set and no --project specified.[/red]")
                console.print("[yellow]Either run 'canvas set default-project <project-name>' or use --project option.[/yellow]")
                raise click.Abort()
        
        # Resolve project ID
        from ..utils.helpers import _resolve_project_id
        project_id = _resolve_project_id(target_project)
        if not project_id:
            console.print(f"[red]Project '{target_project}' not found. Run 'canvas add project {target_project}' first.[/red]")
            raise click.Abort()
        
        console.print(f"[blue]Fetching agents from project '{target_project}'...[/blue]")
        
        # Fetch agents
        agents_data = api_client.list_agents(project_id=project_id)
        
        if not agents_data:
            console.print("[yellow]No agents found.[/yellow]")
            return
        
        # Create table
        table = Table(title=f"Agents in Project: {target_project}", expand=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Short Name", style="magenta", overflow="fold")
        table.add_column("Name", style="bright_white", overflow="fold")
        table.add_column("Description", style="white", overflow="fold")
        table.add_column("Status", style="green", no_wrap=True)
        table.add_column("Created", style="dim", no_wrap=True)
        
        # Add rows
        for agent in agents_data:
            # Truncate description if too long
            description = agent.get("description", "")
            if len(description) > 50:
                description = description[:47] + "..."
            
            # Determine status
            status = "Active" if agent.get("isActive", True) else "Inactive"
            status_style = "green" if agent.get("isActive", True) else "red"
            
            # Format createdAt timestamp
            created_at = agent.get("createdAt")
            if created_at:
                if isinstance(created_at, int):
                    # Convert timestamp to readable date
                    from datetime import datetime
                    created_at_str = datetime.fromtimestamp(created_at / 1000).strftime("%Y-%m-%d")
                else:
                    # Handle string format
                    created_at_str = str(created_at)[:10]
            else:
                created_at_str = "N/A"
            
            table.add_row(
                agent.get("publicId", agent.get("id", "N/A")),  # Use 'id' if 'publicId' not present
                agent.get("shortName", "N/A"),
                agent.get("name", "N/A"),
                description,
                f"[{status_style}]{status}[/{status_style}]",
                created_at_str
            )
        
        console.print(table)
        console.print(f"\n[blue]Total agents:[/blue] {len(agents_data)}")
        
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[yellow]Full stack trace:[/yellow]")
        console.print(traceback.format_exc())
        raise click.Abort()


def _list_local_projects() -> None:
    """List projects that have been added to the local workspace."""
    projects_dir = Path("projects")
    if not projects_dir.exists():
        console.print("[yellow]No projects directory found. Run 'canvas add project <name>' to add projects.[/yellow]")
        return
    
    # Find all project directories
    project_dirs = [d for d in projects_dir.iterdir() if d.is_dir() and (d / "project.yaml").exists()]
    
    if not project_dirs:
        console.print("[yellow]No projects found in workspace. Run 'canvas add project <name>' to add projects.[/yellow]")
        return
    
    # Create table
    table = Table(title="Local Workspace Projects", expand=True)
    table.add_column("Short Name", style="magenta", overflow="fold")
    table.add_column("Name", style="bright_white", overflow="fold") 
    table.add_column("Environment", style="green", no_wrap=True)
    table.add_column("Profile", style="cyan", no_wrap=True)
    table.add_column("Added", style="dim", no_wrap=True)
    table.add_column("Description", style="white", overflow="fold")
    
    # Load and display each project
    for project_dir in sorted(project_dirs):
        try:
            with open(project_dir / "project.yaml", 'r') as f:
                project_data = yaml.safe_load(f) or {}
            
            short_name = project_data.get("shortName", project_dir.name) or project_dir.name
            name = project_data.get("name") or "N/A"
            config = project_data.get("config") or {}
            environment = config.get("environment") or "N/A"
            profile = project_data.get("profile") or "N/A"
            added_at = project_data.get("addedAt") or "N/A"
            description = project_data.get("description") or ""
            
            # Format added date
            if added_at and added_at != "N/A":
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
                    added_at = dt.strftime("%Y-%m-%d")
                except:
                    added_at = "N/A"
            
            # Truncate description
            if description and len(description) > 40:
                description = description[:37] + "..."
            
            table.add_row(
                short_name,
                name,
                environment,
                profile,
                added_at,
                description
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read {project_dir}/project.yaml: {e}[/yellow]")
    
    console.print(table)
    console.print(f"\n[blue]Total local projects:[/blue] {len(project_dirs)}")
    console.print(f"[dim]Use[/dim] [cyan]canvas add project <name>[/cyan] [dim]to add more projects[/dim]")