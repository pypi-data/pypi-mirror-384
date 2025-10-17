"""Main CLI entry point for Raga Canvas CLI."""

import click
import traceback
from rich.console import Console

from .commands.init import init
from .commands.login import login
from .commands.list import list_cmd
from .commands.push import push
from .commands.pull import pull
from .commands.deploy import deploy
from .commands.set import set_group
from .commands.add import add
from .commands.help import help_command
from .commands.certificate import get_group, update_group
from .utils.exceptions import CanvasError

console = Console()


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Canvas CLI - Manage AI projects, agents, tools, and datasources.
    
    Canvas CLI helps you manage your AI development workflow with commands to:
    • Initialize and configure workspaces
    • Pull and push agents, tools, and datasources  
    • Deploy agents to the Canvas platform
    • Manage authentication and profiles
    
    Quick start:
      canvas init my-project     # Initialize workspace
      canvas login              # Authenticate  
      canvas help              # Show detailed help
    
    For detailed help on any command, use: canvas help <command>
    """
    ctx.ensure_object(dict)


# Register commands
cli.add_command(init)
cli.add_command(login)
cli.add_command(list_cmd, name="list")
cli.add_command(push)
cli.add_command(pull)
cli.add_command(deploy)
cli.add_command(set_group, name="set")
cli.add_command(add)
cli.add_command(help_command, name="help")
cli.add_command(get_group, name="get")
cli.add_command(update_group, name="update")

def main() -> None:
    """Main entry point."""
    try:
        cli()
    except CanvasError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        console.print("\n[yellow]Full stack trace:[/yellow]")
        console.print(traceback.format_exc())
        raise click.Abort()


if __name__ == "__main__":
    main()
