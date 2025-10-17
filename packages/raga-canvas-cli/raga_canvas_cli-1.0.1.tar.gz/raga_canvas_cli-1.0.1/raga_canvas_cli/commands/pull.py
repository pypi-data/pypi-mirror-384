"""Pull command for downloading resources from Canvas platform."""
from typing import Optional

import click

from ..operations.pull_project import pull_project_operation
from ..operations.pull_agent import pull_agent_operation


@click.group(name="pull")
def pull() -> None:
    """Pull Canvas resources (agents, tools, datasources, etc.)."""
    pass


# Note: Project management moved to 'canvas add project' command
# This command is deprecated but kept for backward compatibility
@pull.command(name="project", hidden=True)
@click.argument("project_short_name", required=True)
@click.option(
    "--profile",
    help="Profile to use for authentication"
)
def pull_project_deprecated(project_short_name: str, profile: Optional[str]) -> None:
    """[DEPRECATED] Use 'canvas add project' instead."""
    from rich.console import Console
    console = Console()
    console.print("[yellow]Warning:[/yellow] 'canvas pull project' is deprecated.")
    console.print("Use [cyan]canvas add project <name>[/cyan] instead.")
    console.print()
    pull_project_operation(project_short_name, profile)


@pull.command(name="agent")
@click.argument("agent_short_name", required=True)
@click.option(
    "--project",
    help="Project short name to pull from (uses default project if not specified)"
)
@click.option(
    "--agent-short-name",
    help="Agent short name to pull to (uses current directory if not specified)",
    required=True
)
@click.option(
    "--profile",
    help="Profile to use for authentication"
)
def pull_agent_command(agent_short_name: str, project: Optional[str], profile: Optional[str]) -> None:
    """Pull a specific agent by short name to global agents/ directory.

    Examples:
      canvas pull agent my-agent
      canvas pull agent my-agent --project my-project
    """
    pull_agent_operation(agent_short_name, project, profile)