"""Push command for deploying agents to Canvas platform."""
from typing import Optional

import click

from ..operations.push_agent import push_agent_operation


@click.group(name="push")
def push() -> None:
    """Push Canvas resources (agents, tools, datasources, etc.)."""
    pass


@push.command(name="agent")
@click.option(
    "--target-project",
    required=False,
    help="Project ID to push the agent to"
)
@click.option(
    "--agent",
    required=True,
    help="Agent directory name or ID to push"
)
@click.option(
    "--profile",
    help="Profile to use for authentication"
)
@click.option(
    "--force",
    is_flag=True,
    help="Force deployment even if validation warnings exist"
)
def push_agent_command(target_project: str, agent: str, 
         profile: Optional[str], force: bool) -> None:
    """Push a local agent to the Canvas platform.
    
    agent: short name of the agent to deploy (directory name in agents/)
    target_project: Target project short name on the Canvas platform
    """
    push_agent_operation(agent, target_project, profile, force)


# Add singular alias for user convenience
@push.command(name="agent")
@click.argument("agent_name", required=True)
@click.option(
    "--project",
    help="Project short name to push to"
)
@click.option(
    "--profile",
    help="Profile to use for authentication"
)
@click.option(
    "--force",
    is_flag=True,
    help="Force deployment even if validation warnings exist"
)
def push_single_agent_command(agent_name: str, project: Optional[str], 
         profile: Optional[str], force: bool) -> None:
    """Push a local agent to the Canvas platform.
    
    AGENT_NAME: short name of the agent to deploy (directory name in agents/)
    """
    push_agent_operation(agent_name, project, profile, force)