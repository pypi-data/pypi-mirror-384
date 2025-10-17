"""Add command for adding projects to Canvas workspace."""
from typing import Optional

import click

from ..operations.pull_project import pull_project_operation


@click.group(name="add")
def add() -> None:
    """Add projects to your Canvas workspace."""
    pass


@add.command(name="project")
@click.argument("project_short_name", required=True)
@click.option(
    "--profile",
    help="Profile to use for authentication"
)
def add_project(project_short_name: str, profile: Optional[str]) -> None:
    """Add a project to your workspace.
    
    This command connects your workspace to a remote Canvas project by:
    • Downloading project configuration
    • Setting up environment template
    • Storing project metadata locally
    
    Examples:
      canvas add project my-project
      canvas add project my-project --profile production
    """
    pull_project_operation(project_short_name, profile)
