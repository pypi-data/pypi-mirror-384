"""Help operation for Canvas CLI."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

console = Console()


def show_general_help() -> None:
    """Show general Canvas CLI help information."""
    
    # Header
    console.print()
    console.print("[bold blue]Canvas CLI - Command Line Interface[/bold blue]", justify="center")
    console.print("[dim]Manage your Canvas AI projects, agents, tools, and datasources[/dim]", justify="center")
    console.print()
    
    # Usage
    usage_panel = Panel(
        "[bold]canvas[/bold] [cyan]<command>[/cyan] [yellow][options][/yellow]\n\n"
        "Examples:\n"
        "  [dim]canvas init my-project[/dim]\n"
        "  [dim]canvas login[/dim]\n"
        "  [dim]canvas pull agent my-agent[/dim]\n"
        "  [dim]canvas push agent my-agent --project my-project[/dim]",
        title="[bold]Usage[/bold]",
        border_style="blue"
    )
    console.print(usage_panel)
    
    # Commands table
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")
    table.add_column("Command", style="cyan", width=12)
    table.add_column("Description", style="white")
    table.add_column("Example", style="dim")
    
    # Workspace commands
    table.add_row("init", "Initialize a new Canvas workspace", "canvas init my-project")
    table.add_row("login", "Authenticate with Canvas platform", "canvas login")
    table.add_row("set", "Configure workspace settings", "canvas set default-project my-proj")
    
    table.add_section()
    
    # Resource commands
    table.add_row("add", "Add projects to your workspace", "canvas add project my-project")
    table.add_row("list", "List projects, agents, tools, datasources", "canvas list projects --local")
    table.add_row("pull", "Download agents from Canvas", "canvas pull agent my-agent")
    table.add_row("push", "Upload agents to Canvas", "canvas push agent my-agent")
    table.add_row("deploy", "Deploy agents to Canvas platform", "canvas deploy agent my-agent")
    
    table.add_section()
    
    # Help command
    table.add_row("help", "Show detailed help for commands", "canvas help pull")
    
    console.print(table)
    
    # Workflow section
    workflow_panel = Panel(
        "[bold]Quick Start Workflow:[/bold]\n\n"
        "[dim]1.[/dim] [cyan]canvas init my-workspace[/cyan]        # Initialize workspace\n"
        "[dim]2.[/dim] [cyan]canvas login[/cyan]                   # Authenticate\n"
        "[dim]3.[/dim] [cyan]canvas list projects[/cyan]           # See available remote projects\n"
        "[dim]4.[/dim] [cyan]canvas add project my-proj[/cyan]      # Add project to workspace\n"
        "[dim]5.[/dim] [cyan]canvas pull agent my-agent[/cyan]      # Download agent + dependencies\n"
        "[dim]6.[/dim] [cyan]canvas push agent my-agent[/cyan]      # Upload changes\n\n"
        "[yellow]Tip:[/yellow] Use [cyan]canvas list projects --local[/cyan] to see added projects",
        title="[bold]Getting Started[/bold]",
        border_style="green"
    )
    console.print(workflow_panel)
    
    # Additional help
    console.print()
    console.print("[dim]For detailed help on any command, use:[/dim] [cyan]canvas help <command>[/cyan]")
    console.print("[dim]For command-specific options, use:[/dim] [cyan]canvas <command> --help[/cyan]")
    console.print()


def show_command_help(command: str) -> None:
    """Show detailed help for a specific command."""
    
    command_help = {
        "init": _get_init_help(),
        "login": _get_login_help(),
        "add": _get_add_help(),
        "list": _get_list_help(),
        "pull": _get_pull_help(),
        "push": _get_push_help(),
        "deploy": _get_deploy_help(),
        "set": _get_set_help(),
    }
    
    if command in command_help:
        command_help[command]()
    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("\n[dim]Available commands:[/dim]")
        for cmd in sorted(command_help.keys()):
            console.print(f"  [cyan]{cmd}[/cyan]")
        console.print(f"\n[dim]Use[/dim] [cyan]canvas help <command>[/cyan] [dim]for detailed help[/dim]")


def _get_init_help() -> None:
    """Show help for init command."""
    console.print("\n[bold blue]canvas init[/bold blue] - Initialize Canvas Workspace")
    console.print()
    
    # Usage
    usage = Panel(
        "[bold]canvas init[/bold] [yellow]<workspace-name>[/yellow]\n"
        "[bold]canvas init[/bold] [yellow].[/yellow]  [dim]# Use current directory[/dim]",
        title="Usage",
        border_style="blue"
    )
    console.print(usage)
    
    # Description
    console.print("[bold]Description:[/bold]")
    console.print("Creates a new Canvas workspace with the required directory structure:")
    console.print("• [cyan]projects/[/cyan] - Project configurations")
    console.print("• [cyan]agents/[/cyan] - Agent definitions")
    console.print("• [cyan]tools/[/cyan] - Tool configurations")
    console.print("• [cyan]datasources/[/cyan] - Datasource definitions")
    console.print("• [cyan]env/[/cyan] - Environment-specific variables")
    console.print("• [cyan]profiles/[/cyan] - Authentication profiles")
    console.print()
    
    # Examples
    examples = Panel(
        "[cyan]canvas init my-project[/cyan]     # Create new workspace\n"
        "[cyan]canvas init .[/cyan]              # Initialize current directory",
        title="Examples",
        border_style="green"
    )
    console.print(examples)


def _get_login_help() -> None:
    """Show help for login command."""
    console.print("\n[bold blue]canvas login[/bold blue] - Authenticate with Canvas Platform")
    console.print()
    
    # Usage
    usage = Panel(
        "[bold]canvas login[/bold] [yellow][options][/yellow]",
        title="Usage",
        border_style="blue"
    )
    console.print(usage)
    
    # Options
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")
    table.add_column("Option", style="yellow", width=20)
    table.add_column("Description", style="white")
    
    table.add_row("--api-base URL", "Canvas API base URL")
    table.add_row("--profile NAME", "Profile name to save credentials")
    
    console.print(table)
    
    # Description
    console.print("\n[bold]Description:[/bold]")
    console.print("Authenticates with the Canvas platform and saves credentials securely.")
    console.print("Creates a profile configuration for CI/CD workflows.")
    console.print()
    
    # Examples
    examples = Panel(
        "[cyan]canvas login[/cyan]                                    # Interactive login\n"
        "[cyan]canvas login --profile production[/cyan]               # Save as 'production' profile\n"
        "[cyan]canvas login --api-base https://api.canvas.ai[/cyan]   # Custom API endpoint",
        title="Examples",
        border_style="green"
    )
    console.print(examples)


def _get_add_help() -> None:
    """Show help for add command."""
    console.print("\n[bold blue]canvas add[/bold blue] - Add Projects to Workspace")
    console.print()
    
    # Usage
    usage = Panel(
        "[bold]canvas add project[/bold] [yellow]<project-name>[/yellow] [yellow][options][/yellow]",
        title="Usage",
        border_style="blue"
    )
    console.print(usage)
    
    # Subcommands
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")
    table.add_column("Subcommand", style="cyan", width=15)
    table.add_column("Description", style="white")
    table.add_column("Options", style="yellow")
    
    table.add_row("project", "Add a project to your workspace", "--profile")
    
    console.print(table)
    
    # Description
    console.print("\n[bold]Description:[/bold]")
    console.print("Connects your local workspace to a remote Canvas project by:")
    console.print("• [green]Downloading project configuration[/green] and metadata")
    console.print("• [green]Creating environment template[/green] for the project's environment")
    console.print("• [green]Storing profile information[/green] for future operations")
    console.print("• [green]Setting up local project structure[/green]")
    console.print()
    
    # Important note
    note = Panel(
        "[yellow]Note:[/yellow] This doesn't download agents, tools, or datasources.\n"
        "Use [cyan]canvas pull agent <name>[/cyan] to download specific agents with their dependencies.",
        title="[bold]What Gets Added[/bold]",
        border_style="yellow"
    )
    console.print(note)
    
    # Examples
    examples = Panel(
        "[cyan]canvas add project my-project[/cyan]              # Add project to workspace\n"
        "[cyan]canvas add project my-project --profile prod[/cyan] # Add using specific profile\n"
        "[cyan]canvas list projects --local[/cyan]               # View added projects",
        title="Examples",
        border_style="green"
    )
    console.print(examples)


def _get_list_help() -> None:
    """Show help for list command."""
    console.print("\n[bold blue]canvas list[/bold blue] - List Canvas Resources")
    console.print()
    
    # Usage
    usage = Panel(
        "[bold]canvas list[/bold] [cyan]projects[/cyan] [yellow][options][/yellow]\n"
        "[bold]canvas list[/bold] [cyan]agents[/cyan] [yellow][options][/yellow]",
        title="Usage",
        border_style="blue"
    )
    console.print(usage)
    
    # Subcommands
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")
    table.add_column("Subcommand", style="cyan", width=15)
    table.add_column("Description", style="white")
    table.add_column("Key Options", style="yellow")
    
    table.add_row("projects", "List remote or local projects", "--profile, --local")
    table.add_row("agents", "List agents in a project", "--profile, --project")
    
    console.print(table)
    
    # Description
    console.print("\n[bold]Key Features:[/bold]")
    console.print("• [green]Remote projects[/green] - List all projects from Canvas platform")
    console.print("• [green]Local projects[/green] - List projects added to workspace with [cyan]--local[/cyan]")
    console.print("• [green]Project-specific agents[/green] - Use [cyan]--project[/cyan] to specify project, or default project if omitted")
    console.print("• [green]Project details[/green] - Shows profile, environment, and added date for local projects")
    console.print()
    
    # Examples
    examples = Panel(
        "[cyan]canvas list projects[/cyan]                    # List remote projects\n"
        "[cyan]canvas list projects --local[/cyan]           # List projects in workspace\n"
        "[cyan]canvas list agents[/cyan]                      # List agents in default project\n"
        "[cyan]canvas list agents --project my-proj[/cyan]    # List agents in specific project\n"
        "[cyan]canvas list projects --profile prod[/cyan]     # Use specific profile",
        title="Examples",
        border_style="green"
    )
    console.print(examples)


def _get_pull_help() -> None:
    """Show help for pull command."""
    console.print("\n[bold blue]canvas pull[/bold blue] - Download Resources from Canvas")
    console.print()
    
    # Usage
    usage = Panel(
        "[bold]canvas pull agent[/bold] [yellow]<agent-name>[/yellow] [yellow][options][/yellow]",
        title="Usage",
        border_style="blue"
    )
    console.print(usage)
    
    # Subcommands
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")
    table.add_column("Subcommand", style="cyan", width=15)
    table.add_column("Description", style="white")
    table.add_column("Key Options", style="yellow")
    
    table.add_row("agent", "Download agent with dependencies", "--project, --profile")
    
    console.print(table)
    
    # Description
    console.print("\n[bold]Key Features:[/bold]")
    console.print("• [green]Global storage[/green] - Agents, tools, datasources stored globally")
    console.print("• [green]Dependency resolution[/green] - Automatically pulls required tools/datasources")
    console.print("• [green]Environment handling[/green] - Manages environment-specific variables")
    console.print("• [green]System prompt extraction[/green] - Saves prompts to readable text files")
    console.print()
    
    # Important note
    note = Panel(
        "[yellow]Note:[/yellow] Tools and datasources are automatically pulled as dependencies when pulling agents.\n"
        "There are no individual pull commands for tools or datasources.",
        title="[bold]Dependency Management[/bold]",
        border_style="yellow"
    )
    console.print(note)
    
    # Examples
    examples = Panel(
        "[cyan]canvas pull agent my-agent[/cyan]                   # Download agent with all dependencies\n"
        "[cyan]canvas pull agent my-agent --project other-proj[/cyan] # Pull from specific project\n\n"
        "[dim]Note: Use[/dim] [cyan]canvas add project <name>[/cyan] [dim]to add projects to workspace[/dim]",
        title="Examples",
        border_style="green"
    )
    console.print(examples)


def _get_push_help() -> None:
    """Show help for push command."""
    console.print("\n[bold blue]canvas push[/bold blue] - Upload Resources to Canvas")
    console.print()
    
    # Usage
    usage = Panel(
        "[bold]canvas push agent[/bold] [yellow]<agent-name>[/yellow] [yellow][options][/yellow]\n"
        "[bold]canvas push agents[/bold] [yellow]--agent <name>[/yellow] [yellow][options][/yellow]",
        title="Usage",
        border_style="blue"
    )
    console.print(usage)
    
    # Subcommands
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")
    table.add_column("Subcommand", style="cyan", width=15)
    table.add_column("Description", style="white")
    table.add_column("Key Options", style="yellow")
    
    table.add_row("agent", "Upload single agent (singular)", "--project, --profile, --force")
    
    console.print(table)
    
    # Description
    console.print("\n[bold]Key Features:[/bold]")
    console.print("• [green]System prompt handling[/green] - Automatically loads from system_prompt.txt")
    console.print("• [green]Dependency pushing[/green] - Uploads required tools and datasources automatically")
    console.print("• [green]Validation[/green] - Validates configuration before upload")
    console.print("• [green]Environment variables[/green] - Loads from environment-specific YAML")
    console.print()
    
    # Important note
    note = Panel(
        "[yellow]Note:[/yellow] Tools and datasources are pushed automatically as agent dependencies.\n"
        "Only agents need to be pushed individually - their tools and datasources are included automatically.",
        title="[bold]Automatic Dependency Management[/bold]",
        border_style="yellow"
    )
    console.print(note)
    
    # Examples
    examples = Panel(
        "[cyan]canvas push agent my-agent[/cyan]                      # Upload agent with all dependencies\n"
        "[cyan]canvas push agent my-agent --project target-proj[/cyan] # Upload to specific project\n"
        "[cyan]canvas push agent my-agent --force[/cyan]               # Skip validation warnings",
        title="Examples",
        border_style="green"
    )
    console.print(examples)


def _get_deploy_help() -> None:
    """Show help for deploy command."""
    console.print("\n[bold blue]canvas deploy[/bold blue] - Deploy Agents to Canvas Platform")
    console.print()
    
    # Usage
    usage = Panel(
        "[bold]canvas deploy agent[/bold] [yellow]<agent-name>[/yellow] [yellow][options][/yellow]",
        title="Usage",
        border_style="blue"
    )
    console.print(usage)
    
    # Options
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")
    table.add_column("Option", style="yellow", width=20)
    table.add_column("Description", style="white")
    
    table.add_row("--project", "Target project for deployment")
    table.add_row("agent-name", "Name of the agent to deploy (argument)")
    table.add_row("--profile", "Authentication profile to use")
    
    console.print(table)
    
    # Examples
    examples = Panel(
        "[cyan]canvas deploy agent my-agent --project prod[/cyan]",
        title="Examples",
        border_style="green"
    )
    console.print(examples)


def _get_set_help() -> None:
    """Show help for set command."""
    console.print("\n[bold blue]canvas set[/bold blue] - Configure Workspace Settings")
    console.print()
    
    # Usage
    usage = Panel(
        "[bold]canvas set default-project[/bold] [yellow]<project-name>[/yellow]",
        title="Usage",
        border_style="blue"
    )
    console.print(usage)
    
    # Subcommands
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")
    table.add_column("Subcommand", style="cyan", width=20)
    table.add_column("Description", style="white")
    
    table.add_row("default-project", "Set the default project for the workspace")
    
    console.print(table)
    
    # Examples
    examples = Panel(
        "[cyan]canvas set default-project my-project[/cyan]   # Set default project",
        title="Examples",
        border_style="green"
    )
    console.print(examples)


def show_workspace_structure_help() -> None:
    """Show help about workspace structure."""
    console.print("\n[bold blue]Canvas Workspace Structure[/bold blue]")
    console.print()
    
    structure = """[bold]Canvas Workspace Directory Structure:[/bold]

[cyan]my-workspace/[/cyan]
├── [yellow]canvas.yaml[/yellow]          # Workspace configuration
├── [cyan]projects/[/cyan]               # Project configurations
│   └── [cyan]my-project/[/cyan]
│       └── [yellow]project.yaml[/yellow]    # Project metadata
├── [cyan]agents/[/cyan]                 # Global agent definitions
│   └── [cyan]my-agent/[/cyan]
│       ├── [yellow]agent.yaml[/yellow]       # Agent configuration
│       └── [yellow]system_prompt.txt[/yellow] # Human-readable prompt
├── [cyan]tools/[/cyan]                  # Global tool definitions
│   └── [cyan]my-tool/[/cyan]
│       └── [yellow]tool.yaml[/yellow]        # Tool configuration
├── [cyan]datasources/[/cyan]            # Global datasource definitions
│   └── [cyan]my-datasource/[/cyan]
│       └── [yellow]datasource.yaml[/yellow]  # Datasource configuration
├── [cyan]env/[/cyan]                    # Environment variables (gitignored)
│   ├── [yellow]dev.yaml[/yellow]            # Development variables
│   └── [yellow]prod.yaml[/yellow]           # Production variables
└── [cyan]profiles/[/cyan]               # Authentication profiles (for CI/CD)
    └── [yellow]default.yaml[/yellow]        # Profile configuration (no secrets)
"""
    
    panel = Panel(structure, title="[bold]Directory Structure[/bold]", border_style="blue")
    console.print(panel)
    
    # Key concepts
    concepts = Panel(
        "[bold]Key Concepts:[/bold]\n\n"
        "• [green]Global Resources[/green] - Agents, tools, datasources are stored globally\n"
        "• [green]Environment Separation[/green] - env/ files are gitignored for security\n"
        "• [green]Profile Sharing[/green] - profiles/ synced for CI/CD (no secrets)\n"
        "• [green]Human Readable[/green] - System prompts in .txt files for easy editing",
        title="[bold]Design Principles[/bold]",
        border_style="green"
    )
    console.print(concepts)
