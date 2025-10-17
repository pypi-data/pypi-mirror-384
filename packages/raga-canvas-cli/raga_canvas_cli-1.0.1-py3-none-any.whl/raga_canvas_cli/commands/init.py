"""Initialize command for creating Canvas workspace structure."""

import os
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console

from ..utils.config import ConfigManager, CanvasConfig
from ..utils.exceptions import FileSystemError

console = Console()


@click.command()
@click.option(
    "--force",
    is_flag=True,
    help="Force initialization even if files exist"
)
@click.argument("repo_name", required=True)
def init(repo_name: str, force: bool) -> None:
    """Initialize Canvas workspace directory structure."""
    
    try:
        # Determine workspace directory from argument (supports '.' or a folder name)
        if repo_name == ".":
            workspace_path = Path.cwd()
            project_name = workspace_path.name
        else:
            workspace_path = Path.cwd() / repo_name
            project_name = repo_name
            
        console.print(f"[blue]Initializing Canvas workspace:[/blue] {workspace_path}")
        
        # Create workspace directory if it doesn't exist
        if not workspace_path.exists():
            workspace_path.mkdir(parents=True, exist_ok=True)
            console.print("[green]✓[/green] Created workspace directory")
        else:
            console.print("[yellow]•[/yellow] Workspace directory already exists")
            
        # Check if workspace already initialized (unless force is used)
        canvas_yaml = workspace_path / "canvas.yaml"
        if canvas_yaml.exists() and not force:
            console.print("[red]Canvas workspace already initialized. Use --force to reinitialize.[/red]")
            return
                
        # Create directory structure
        _create_directory_structure(workspace_path)

        # Create configuration files
        _create_config_files(workspace_path, project_name)

        # Create sample environment files
        _create_sample_env_files(workspace_path / "env")
                        
        # Update .gitignore
        _update_gitignore(workspace_path)
        
        console.print(f"[green]✓[/green] Canvas workspace '{project_name}' initialized successfully!")
        console.print("\n[blue]Next steps:[/blue]")
        console.print("• Run [cyan]canvas login[/cyan] to authenticate with Canvas platform")
        console.print("• Run [cyan]canvas list projects[/cyan] to see available projects")
                
    except Exception as e:
        raise FileSystemError(f"Failed to initialize workspace: {e}")


def _create_directory_structure(base_path: Path) -> None:
    """Create the Canvas directory structure."""
    directories = [
        "projects",
        "agents",
        "tools", 
        "datasources",
        "env",
        "profiles"
    ]
    
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] Created directory: {directory}")


def _create_config_files(base_path: Path, project_name: str) -> None:
    """Create configuration files."""
    
    # Create canvas.yaml
    canvas_config = CanvasConfig(
        name=project_name,
        version="1.0",
        default_environment="dev"
    )
    
    config_manager = ConfigManager()
    config_manager.workspace_config = base_path / "canvas.yaml"
    config_manager.save_workspace_config(canvas_config)
    console.print("[green]✓[/green] Created canvas.yaml")
    

def _create_sample_env_files(base_path: Path) -> None:
    """Create empty environment template files."""
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Create empty dev.yaml template
    dev_file = base_path / "dev.yaml"
    with open(dev_file, 'w') as f:
        f.write("# Environment variables for dev environment\n")
        f.write("# This file can be shared across multiple projects\n")
        f.write("# Add your development-specific variables below\n")
        f.write("#\n")
        f.write("# Example:\n")
        f.write("# API_BASE_URL: https://api-dev.example.com\n")
        f.write("# DATABASE_URL: postgresql://user:pass@dev-db.example.com/db\n")
        f.write("# DEBUG: true\n")
    console.print("[green]✓[/green] Created dev.yaml")
    
    # Create empty prod.yaml template
    prod_file = base_path / "prod.yaml"
    with open(prod_file, 'w') as f:
        f.write("# Environment variables for prod environment\n")
        f.write("# This file can be shared across multiple projects\n")
        f.write("# Add your production-specific variables below\n")
        f.write("#\n")
        f.write("# Example:\n")
        f.write("# API_BASE_URL: https://api.example.com\n")
        f.write("# DATABASE_URL: postgresql://user:pass@prod-db.example.com/db\n")
        f.write("# DEBUG: false\n")
    console.print("[green]✓[/green] Created prod.yaml")

def _update_gitignore(base_path: Path) -> None:
    """Update .gitignore to ignore sensitive files while allowing profiles/ directory."""
    gitignore_path = base_path / ".gitignore"
    
    gitignore_entries = [
        "# Canvas CLI",
        ".canvasrc",
        "*.lock.json",
        "__pycache__/",
        "*.pyc",
        ".env",
        ".venv/",
        "node_modules/",
        "",
        "# Environment files - should not be committed",
        "env/",
        "",
        "# Profiles directory is synced for CI/CD",
        "# but credentials are stored securely elsewhere",
        "# profiles/ - DO NOT ignore this directory",
    ]
    
    existing_content = ""
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            existing_content = f.read()
    
    # Only add entries that don't already exist
    new_entries = []
    for entry in gitignore_entries:
        if entry not in existing_content:
            new_entries.append(entry)
    
    if new_entries:
        with open(gitignore_path, 'a') as f:
            if existing_content and not existing_content.endswith('\n'):
                f.write('\n')
            f.write('\n'.join(new_entries) + '\n')
        console.print("[green]✓[/green] Updated .gitignore")
    else:
        console.print("[yellow]•[/yellow] .gitignore already up to date")
