"""Update certificate operation for Canvas CLI."""

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


def update_certificate_operation(project: Optional[str], profile: Optional[str], public_key_path: str) -> None:
    """Update JWT public key certificate for a project."""
    try:
        # Validate we're in a Canvas workspace
        require_canvas_workspace()
        
        # Validate authentication
        require_authentication(profile)
        
        # Validate public key file exists
        key_file = Path(public_key_path)
        if not key_file.exists():
            console.print(f"[red]Public key file not found:[/red] {public_key_path}")
            raise click.Abort()
        
        # Read the public key file
        try:
            with open(key_file, 'r') as f:
                public_key_content = f.read()
        except Exception as e:
            console.print(f"[red]Failed to read public key file:[/red] {e}")
            raise click.Abort()
        
        if not public_key_content.strip():
            console.print("[red]Public key file is empty[/red]")
            raise click.Abort()
        
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
        
        # Load project.yaml to get project ID
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
        
        console.print(f"[blue]Updating JWT public key for project '{project}'...[/blue]")
        
        # Update the JWT public key
        result = api_client.update_project_jwt_public_key(project_id, public_key_content)
        
        # Handle both dict and list responses
        if isinstance(result, list):
            result = result[0] if result else {}
        
        # Display success message
        console.print(f"\n[green]✓[/green] JWT signing key updated successfully for project '{project}'!")
        
        # Display what it was set to
        updated_key = result.get("publicKey", "") if isinstance(result, dict) else ""
        if updated_key:
            console.print("\n[blue]Updated public key:[/blue]")
            console.print("[dim]" + "="*60 + "[/dim]")
            # Show first few lines
            key_lines = updated_key.split('\n')
            preview_lines = key_lines[:5]
            console.print('\n'.join(preview_lines))
            if len(key_lines) > 5:
                console.print("[dim]... (truncated)[/dim]")
            console.print("[dim]" + "="*60 + "[/dim]")
        
        # Update local project.yaml to reflect hasJwtSigningKey = true
        try:
            project_data["hasJwtSigningKey"] = True
            with open(project_file, 'w') as f:
                yaml.safe_dump(project_data, f, default_flow_style=False, allow_unicode=True)
            console.print(f"\n[green]✓[/green] Updated local project configuration")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not update local project.yaml: {e}")
        
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}")
        raise click.Abort()
    except FileSystemError as e:
        console.print(f"[red]File Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

