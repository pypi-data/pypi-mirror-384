"""Certificate commands for managing JWT signing keys."""
from typing import Optional

import click

from ..operations.get_certificate import get_certificate_operation
from ..operations.update_certificate import update_certificate_operation


@click.group(name="get")
def get_group() -> None:
    """Get information from Canvas platform."""
    pass


@click.group(name="update")
def update_group() -> None:
    """Update information on Canvas platform."""
    pass


@get_group.command(name="project-certificate")
@click.option(
    "--project",
    help="Project short name to get certificate for (uses default project if not specified)"
)
@click.option(
    "--profile",
    help="Profile to use for authentication"
)
def get_project_certificate(project: Optional[str], profile: Optional[str]) -> None:
    """Get JWT public key certificate for a project.
    
    This command retrieves the JWT public key configured for the specified project.
    The key is used for validating JWT tokens issued by the project.
    
    Examples:
      canvas get project-certificate
      canvas get project-certificate --project my-project
    """
    get_certificate_operation(project, profile)


@update_group.command(name="project-certificate")
@click.option(
    "--project",
    help="Project short name to update certificate for (uses default project if not specified)"
)
@click.option(
    "--profile",
    help="Profile to use for authentication"
)
@click.option(
    "--public-key",
    required=True,
    help="Path to the public key PEM file"
)
def update_project_certificate(project: Optional[str], profile: Optional[str], public_key: str) -> None:
    """Update JWT public key certificate for a project.
    
    This command uploads a new JWT public key for the specified project.
    The key should be in PEM format.
    
    Examples:
      canvas update project-certificate --public-key ./public_key.pem
      canvas update project-certificate --project my-project --public-key ./key.pem
    """
    update_certificate_operation(project, profile, public_key)

