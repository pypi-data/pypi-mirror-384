"""Deploy command for deploying agents to Canvas platform."""
from typing import Optional

import click

from ..operations.deploy_agent import deploy_agent_operation


@click.group(name="deploy")
def deploy() -> None:
    """Deploy Canvas agents."""
    pass


@deploy.command(name="agent")
@click.argument("agent_name", required=True)
@click.option(
    "--project",
    help="Project short name to deploy to (uses default project if not specified)"
)
@click.option(
    "--profile",
    help="Profile to use for authentication"
)
def deploy_agent(agent_name: str, project: Optional[str], profile: Optional[str]) -> None:
    """Deploy an agent to the Canvas platform.
    
    AGENT_NAME: short name or ID of the agent to deploy
    
    Examples:
      canvas deploy agent my-agent
      canvas deploy agent my-agent --project my-project
    """
    deploy_agent_operation(project, agent_name, profile)