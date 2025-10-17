"""Pull project operation for Canvas CLI."""

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


def _validate_environment_name(environment: str) -> bool:
    """Validate environment name: no spaces, lowercase, starts with letters."""
    import re
    # Must start with letter, contain only lowercase letters, numbers, hyphens, underscores
    # No spaces allowed
    pattern = r'^[a-z][a-z0-9_-]*$'
    return bool(re.match(pattern, environment.strip()))


def pull_project_operation(project_short_name: str, profile: Optional[str]) -> None:
    """Pull a specific project by short name into projects/ directory."""
    try:
        # Validate we're in a Canvas workspace
        require_canvas_workspace()
        
        # Validate authentication
        require_authentication(profile)
        
        config_manager = ConfigManager()
        user_profile = config_manager.get_profile(profile)

        api_client = APIClient(user_profile)
        
        # Find the specific project by short name
        projects = api_client.list_projects()
        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            return
            
        target_project = None
        for project in projects:
            if project.get("shortName") == project_short_name:
                target_project = project
                break
                
        if not target_project:
            console.print(f"[red]Project '{project_short_name}' not found.[/red]")
            return
            
        # Create projects directory if it doesn't exist
        projects_dir = Path("projects")
        projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle environment configuration
        project_config_data = target_project.get("config", {})
        environment = project_config_data.get("environment")
        
        # If environment is empty or invalid, prompt user for it
        if not environment or not _validate_environment_name(environment):
            if environment and not _validate_environment_name(environment):
                console.print(f"[yellow]Warning: Invalid environment name '{environment}' in project config.[/yellow]")
            from rich.prompt import Prompt
            while True:
                environment = Prompt.ask(
                    f"Environment for project '{project_short_name}' (e.g., dev, staging, prod, dev1, sandbox)",
                    default="dev"
                )
                if _validate_environment_name(environment):
                    break
                else:
                    console.print("[red]Invalid environment name.[/red]")
                    console.print("[yellow]Environment name must:[/yellow]")
                    console.print("• Start with a letter")
                    console.print("• Contain only lowercase letters, numbers, hyphens, underscores")
                    console.print("• Have no spaces")
                    console.print("[blue]Examples: dev, staging, prod, dev1, dev-east, sandbox_v2[/blue]")
            
            # Update the project config with user-provided environment
            project_config_data["environment"] = environment
        
        # Create project directory (like other resources)
        project_dir = projects_dir / project_short_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create project.yaml file inside project directory
        project_config = {
            "id": target_project.get("id") or target_project.get("publicId"),
            "shortName": target_project.get("shortName"),
            "name": target_project.get("name"),
            "description": target_project.get("description"),
            "config": project_config_data,
            "hasJwtSigningKey": target_project.get("hasJwtSigningKey", False),
            "profile": profile or "default",  # Store the profile used to add this project
            "addedAt": None  # Will be set to current timestamp
        }
        
        # Add timestamp
        from datetime import datetime
        project_config["addedAt"] = datetime.utcnow().isoformat() + "Z"
        
        project_file = project_dir / "project.yaml"
        with open(project_file, 'w') as f:
            yaml.safe_dump(project_config, f, default_flow_style=False)
            
        # Create environment directory and template file if it doesn't exist
        env_dir = Path("env")
        env_dir.mkdir(parents=True, exist_ok=True)
        
        env_file = env_dir / f"{environment}.yaml"
        
        # Only create environment file if it doesn't exist (keep it as empty template)
        # Multiple projects can use the same environment file
        if not env_file.exists():
            # Create empty environment template (no project-specific data)
            with open(env_file, 'w') as f:
                f.write(f"# Environment variables for {environment} environment\n")
                f.write("# This file can be shared across multiple projects\n")
                f.write("# Add your environment-specific variables below\n")
                f.write("#\n")
                f.write("# Example:\n")
                f.write("# API_BASE_URL: https://api.example.com\n")
                f.write("# DATABASE_URL: postgresql://user:pass@db.example.com/db\n")
                f.write("# API_TOKEN: ${SECRET_API_TOKEN}\n")
                f.write("# DEBUG: true\n")
            
            console.print(f"[green]✓[/green] Created environment template: {env_file}")
        else:
            console.print(f"[blue]Environment file already exists: {env_file}[/blue]")
            
        console.print(f"[green]✓[/green] Added project '{project_short_name}' to workspace")
        console.print(f"[blue]Project configuration saved to:[/blue] projects/{project_short_name}/project.yaml")
        console.print(f"[blue]Environment template created:[/blue] env/{environment}.yaml")
        console.print()
        console.print(f"[blue]Next steps:[/blue]")
        console.print(f"• Run [cyan]canvas pull agent <agent-name> --project {project_short_name}[/cyan] to download agents")
        console.print(f"• Edit [cyan]env/{environment}.yaml[/cyan] to configure environment-specific variables")
        console.print(f"• Use [cyan]canvas list projects --local[/cyan] to see all added projects")
        console.print(f"• Use [cyan]canvas set default-project {project_short_name}[/cyan] to set this project as the default project")
        console.print()
        console.print(f"[yellow]Note:[/yellow] Environment files in env/ are not committed to version control")
        
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}")
        raise click.Abort()
    except FileSystemError as e:
        console.print(f"[red]File Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
