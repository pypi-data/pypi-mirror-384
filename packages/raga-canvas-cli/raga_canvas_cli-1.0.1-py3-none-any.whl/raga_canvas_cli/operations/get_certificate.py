"""Get certificate operation for Canvas CLI."""

import yaml
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ..utils.config import ConfigManager
from ..utils.exceptions import APIError, FileSystemError
from ..services.api_client import APIClient
from ..utils.helpers import require_canvas_workspace, require_authentication

console = Console()


def get_certificate_operation(project: Optional[str], profile: Optional[str]) -> None:
    """Get JWT public key certificate for a project."""
    try:
        # Validate we're in a Canvas workspace
        require_canvas_workspace()
        
        # Validate authentication
        require_authentication(profile)
        
        # Get profile and API client
        config_manager = ConfigManager()
        user_profile = config_manager.get_profile(profile)
        api_client = APIClient(user_profile)
        
        # Determine which project to use
        if not project:
            project = config_manager.get_default_project()
            if not project:
                console.print("[red]No default project set and no --project specified.[/red]")
                console.print("[yellow]Either run 'canvas set default-project <project-name>' or use --project option.[/yellow]")
                raise click.Abort()
        
        # Load project.yaml to get project ID and check hasJwtSigningKey
        project_dir = Path("projects") / project
        project_file = project_dir / "project.yaml"
        
        if not project_file.exists():
            console.print(f"[red]Project '{project}' not found locally.[/red]")
            console.print(f"[yellow]Run 'canvas add project {project}' first.[/yellow]")
            raise click.Abort()
        
        with open(project_file, 'r') as f:
            project_data = yaml.safe_load(f) or {}
        
        project_id = project_data.get("id")
        if not project_id:
            console.print(f"[red]Project ID not found in {project_file}[/red]")
            raise click.Abort()
        
        # Check if JWT signing key is configured
        has_jwt_signing_key = project_data.get("hasJwtSigningKey", False)
        
        if not has_jwt_signing_key:
            console.print(f"[yellow]No JWT signing key has been set for project '{project}'[/yellow]")
            console.print(f"[blue]To set a signing key, run:[/blue] canvas update project-certificate --project {project} --public-key <path-to-key.pem>")
            return
        
        console.print(f"[blue]Fetching JWT public key for project '{project}'...[/blue]")
        
        # Get the JWT public key
        result = api_client.get_project_jwt_public_key(project_id)
        
        # Handle both dict and list responses
        if isinstance(result, list):
            if not result:
                console.print("[yellow]No JWT public key found.[/yellow]")
                return
            # Take the first item if it's a list
            result = result[0] if result else {}
        
        if not result:
            console.print("[yellow]No JWT public key found.[/yellow]")
            return
        
        # Display the public key
        public_key = result.get("publicKey", "") if isinstance(result, dict) else ""
        
        if public_key:
            console.print(f"\n[green]✓[/green] JWT Public Key for project '{project}':")
            console.print("[dim]" + "="*60 + "[/dim]")
            console.print(public_key)
            console.print("[dim]" + "="*60 + "[/dim]")
        else:
            console.print("[yellow]Public key is empty.[/yellow]")
        
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}")
        raise click.Abort()
    except FileSystemError as e:
        console.print(f"[red]File Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

