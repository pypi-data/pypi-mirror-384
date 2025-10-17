"""Help command for Canvas CLI."""
from typing import Optional

import click

from ..operations.help import show_general_help, show_command_help, show_workspace_structure_help


@click.command()
@click.argument("command", required=False)
@click.option(
    "--structure",
    is_flag=True,
    help="Show workspace directory structure"
)
def help_command(command: Optional[str], structure: bool) -> None:
    """Show help information for Canvas CLI commands.
    
    COMMAND: specific command to show help for (optional)
    
    Examples:
      canvas help
      canvas help pull
      canvas help --structure
    """
    if structure:
        show_workspace_structure_help()
    elif command:
        show_command_help(command)
    else:
        show_general_help()


# Also create an alias that works as a standalone command
help = help_command
