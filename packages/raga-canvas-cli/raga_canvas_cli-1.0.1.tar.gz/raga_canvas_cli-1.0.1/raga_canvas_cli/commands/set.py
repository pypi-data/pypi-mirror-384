import click
from pathlib import Path
from rich.console import Console
from typing import Optional
from ..utils.config import ConfigManager, CanvasConfig
from ..utils.exceptions import FileSystemError, ConfigurationError
from ..utils.helpers import require_canvas_workspace

console = Console()


@click.group(name="set")
def set_group() -> None:
    """Set workspace-level defaults."""
    pass


@set_group.command(name="default-project")
@click.argument("project_short_name", required=True)
def set_default_project(project_short_name: str) -> None:
    """Set the default project short name in canvas.yaml (updates 'name')."""
    # Validate we're in a Canvas workspace
    require_canvas_workspace()
    
    try:
        config_manager = ConfigManager()
        config_manager.workspace_config = Path("canvas.yaml")
        cfg = config_manager.load_workspace_config()
        if not cfg:
            console.print("[red]No workspace configuration found. Run 'canvas init' first.[/red]")
            raise click.Abort()
        cfg.name = project_short_name
        config_manager.save_workspace_config(cfg)
        console.print(f"[green]✓[/green] Updated canvas.yaml name to: {project_short_name}")
    except (FileSystemError, ConfigurationError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise click.Abort() 