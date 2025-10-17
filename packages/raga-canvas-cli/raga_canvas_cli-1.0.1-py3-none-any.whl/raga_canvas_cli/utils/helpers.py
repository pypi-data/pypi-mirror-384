"""Helper utilities for Canvas CLI."""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import yaml
import click
from rich.console import Console

console = Console()


def validate_canvas_workspace() -> bool:
    """Validate that the current directory is a Canvas workspace.
    
    Returns:
        bool: True if valid workspace, False otherwise
    """
    canvas_yaml = Path("canvas.yaml")
    if not canvas_yaml.exists():
        console.print("[red]Error:[/red] Not in a Canvas workspace directory.")
        console.print("[yellow]canvas.yaml not found in current directory.[/yellow]")
        console.print("\n[blue]To fix this:[/blue]")
        console.print("• Run [cyan]canvas init <workspace-name>[/cyan] to create a new workspace")
        console.print("• Or navigate to an existing Canvas workspace directory")
        return False
    return True


def require_canvas_workspace():
    """Decorator/helper that validates Canvas workspace and exits if invalid."""
    if not validate_canvas_workspace():
        raise click.Abort()


def validate_authentication(profile: Optional[str] = None) -> bool:
    """Validate that the user is authenticated.
    
    Args:
        profile: Optional profile name to check
        
    Returns:
        bool: True if authenticated, False otherwise
    """
    from ..utils.config import ConfigManager
    
    config_manager = ConfigManager()
    user_profile = config_manager.get_profile(profile)
    
    if not user_profile:
        console.print("[red]Error:[/red] Not authenticated with Canvas platform.")
        console.print("[yellow]No authentication profile found.[/yellow]")
        console.print("\n[blue]To fix this:[/blue]")
        console.print("• Run [cyan]canvas login[/cyan] to authenticate with Canvas platform")
        if profile:
            console.print(f"• Or run [cyan]canvas login --profile {profile}[/cyan] for specific profile")
        return False
        
    if not user_profile.token:
        console.print("[red]Error:[/red] Authentication token not found.")
        console.print(f"[yellow]Profile '{user_profile.name}' exists but has no valid token.[/yellow]")
        console.print("\n[blue]To fix this:[/blue]")
        console.print("• Run [cyan]canvas login[/cyan] to re-authenticate")
        return False
        
    return True


def require_authentication(profile: Optional[str] = None):
    """Decorator/helper that validates authentication and exits if invalid."""
    if not validate_authentication(profile):
        raise click.Abort()


def format_timestamp(timestamp: Optional[str]) -> str:
    """Format ISO timestamp to human readable format."""
    if not timestamp:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return timestamp[:19] if len(timestamp) >= 19 else timestamp


def validate_name(name: str) -> bool:
    """Validate that a name follows Canvas naming conventions."""
    # Names should be alphanumeric with hyphens and underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, name)) and len(name) <= 50


def sanitize_name(name: str) -> str:
    """Sanitize a name to follow Canvas naming conventions."""
    # Replace spaces and special chars with hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '-', name)
    # Remove multiple consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')
    # Limit length
    return sanitized[:50]


def find_canvas_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find the root of a Canvas workspace by looking for canvas.yaml."""
    if start_path is None:
        start_path = Path.cwd()
    
    current = start_path.resolve()
    
    while current != current.parent:
        if (current / "canvas.yaml").exists():
            return current
        current = current.parent
    
    return None


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """Get relative path from base path."""
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        return str(file_path)


def expand_environment_variables(text: str, env_vars: Optional[Dict[str, str]] = None) -> str:
    """Expand environment variables in text."""
    if env_vars is None:
        env_vars = dict(os.environ)
    
    # Replace ${VAR} and $VAR patterns
    def replace_var(match):
        var_name = match.group(1) or match.group(2)
        return env_vars.get(var_name, match.group(0))
    
    # Match ${VAR} or $VAR patterns
    pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
    return re.sub(pattern, replace_var, text)


def deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if (key in result and 
            isinstance(result[key], dict) and 
            isinstance(value, dict)):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))


def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing invalid characters."""
    # Remove or replace invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    return filename[:255] if len(filename) > 255 else filename


def _resolve_project_id(project_short_name: str) -> Optional[str]:
    """Read project YAML file and return the project id, or None if missing."""
    try:
        # Load from projects/{project_short_name}/project.yaml
        project_dir = Path.cwd() / "projects" / project_short_name
        project_file = project_dir / "project.yaml"
        if project_file.exists():
            with open(project_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            project_id = data.get("id")
            if not project_id:
                print(f"[red]Project id not found in {project_file}.\nExpected key: id[/red]")
                return None
            return project_id
        
        # Project not found
        print(f"[red]Project '{project_short_name}' not found.[/red]")
        print(f"[yellow]Run 'canvas pull project {project_short_name}' to download project configuration.[/yellow]")
        return None
        
    except Exception as e:
        print(f"[red]Error reading project config: {e}[/red]")
        return None




def convert_agent_obj_to_agent_data(agent_obj: Dict[str, Any]) -> Dict[str, Any]:
    return agent_obj.get("agentConfig", {})


def convert_tool_obj_to_tool_data(tool_obj: Dict[str, Any]) -> Dict[str, Any]:
    tool_data = tool_obj.get("toolConfig", {})
    tool_data["name"] = tool_obj.get("name")
    tool_data["type"] = tool_obj.get("type")
    return tool_data


def convert_datasource_obj_to_datasource_data(datasource_obj: Dict[str, Any]) -> Dict[str, Any]:
    datasource_data = {}
    datasource_data["name"] = datasource_obj.get("name")
    datasource_data["type"] = datasource_obj.get("type")
    datasource_data["config"] = datasource_obj.get("config", {})
    return datasource_data
