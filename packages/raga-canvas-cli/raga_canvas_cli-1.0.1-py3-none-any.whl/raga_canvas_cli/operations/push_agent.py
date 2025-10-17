"""Push agent operation for Canvas CLI."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import click
from rich.console import Console

from ..utils.config import ConfigManager
from ..utils.exceptions import ValidationError, APIError, FileSystemError
from ..services.api_client import APIClient
from ..utils.helpers import _resolve_project_id, require_canvas_workspace
from .pull_resources import pull_agents

console = Console()


def _get_project_environment(project: str) -> str:
    """Get environment from project configuration."""
    environment = "dev"  # default fallback
    try:
        # Get environment from project config
        project_dir = Path("projects") / project
        project_file = project_dir / "project.yaml"
        if project_file.exists():
            with open(project_file, 'r') as f:
                project_data = yaml.safe_load(f) or {}
            environment = project_data.get("config", {}).get("environment", "dev")
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not determine environment from project config: {e}")
        environment = "dev"
    
    return environment


def load_env_variables_from_yaml(environment: str) -> Dict[str, Any]:
    """Load environment variables from YAML file for variable replacement."""
    env_file_path = Path("env") / f"{environment}.yaml"
    secret_env_file_path = Path("secrets") / f"{environment}.yaml"
    if not env_file_path.exists() and not secret_env_file_path.exists():
        return {}
    env_vars = {}
    try:
        if env_file_path.exists():
            with open(env_file_path, 'r') as f:
                env_data = yaml.safe_load(f) or {}
                # Filter out comment keys and None values
                env_vars.update({k: v for k, v in env_data.items() if not k.startswith("#") and v is not None})
        if secret_env_file_path.exists():
            with open(secret_env_file_path, 'r') as f:
                secret_env_data = yaml.safe_load(f) or {}
                # Filter out comment keys and None values
                env_vars.update({k: v for k, v in secret_env_data.items() if not k.startswith("#") and v is not None})
        
        return env_vars
    
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Failed to load environment variables: {e}")
        return {}


def _load_env_from_environments_dir(target_project: str) -> None:
    """Load environment variables from project's environment YAML file."""
    # Get the project's environment
    environment = _get_project_environment(target_project)
    
    # Load environment variables from the environment-specific YAML file
    env_vars = load_env_variables_from_yaml(environment)
    
    # Set environment variables that aren't already set
    for key, value in env_vars.items():
        if value is not None and key not in os.environ:
            os.environ[key] = str(value)


def _load_agent_config(agent_dir: Path, agent_name: str) -> Dict[str, Any]:
    """Load and merge agent configuration from the per-project folder."""
    
    agent_yaml = agent_dir / "agent.yaml"
    if not agent_dir.exists() or not agent_yaml.exists():
        raise FileSystemError(f"Agent configuration '{agent_yaml}' not found")
    
    with open(agent_yaml, 'r') as f:
        agent_config = yaml.safe_load(f)
    
    # Load system prompt from separate file if it exists
    system_prompt_file = agent_dir / "system_prompt.txt"
    if system_prompt_file.exists():
        with open(system_prompt_file, 'r', encoding='utf-8') as f:
            system_prompt = f.read().strip()
        
        # Add system prompt to config in the expected format
        if "promptConfig" not in agent_config:
            agent_config["promptConfig"] = {}
        agent_config["promptConfig"]["systemPrompt"] = system_prompt
        
        console.print(f"[green]✓[/green] Loaded system prompt from {system_prompt_file}")
    
    return agent_config


def _validate_agent_config(agent_config: Dict[str, Any], force: bool) -> None:
    """Validate agent configuration."""
    
    errors = []
    warnings = []
    
    # Required fields
    required_fields = ["agentName", "description", "agentType", "modelConfig", "promptConfig"]
    for field in required_fields:
        if field not in agent_config:
            errors.append(f"Missing required field: {field}")
    
    # Validate config section
    config = agent_config.get("modelConfig", {})
    if not config.get("model"):
        errors.append("No model specified in modelConfig")
    
    prompt_config = agent_config.get("promptConfig", {})
    if not prompt_config.get("systemPrompt"):
        errors.append("No system prompt specified")
    
    # Validate tools
    tools = agent_config.get("tools", [])
    for tool in tools:
        if not isinstance(tool, str):
            errors.append(f"Tool {tool} is not a string")
    
    # Validate datasources
    tracing_config_id = agent_config.get("tracingConfigId", "")
    if tracing_config_id:
        if not isinstance(tracing_config_id, str):
            errors.append("tracing config ID must be a string")
    
    # Report errors
    if errors:
        console.print("[red]Validation Errors:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        raise ValidationError("Agent configuration has validation errors")
    
    # Report warnings
    if warnings:
        console.print("[yellow]Validation Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  • {warning}")
        
        if not force and not click.confirm("Continue with warnings?", default=True):
            raise click.Abort()


def _resolve_references(local_agent_config: Dict[str, Any], api_client: APIClient, target_project_id: str) -> Dict[str, Any]:
    """Resolve agent references to IDs."""
    subagent_list = []
    for subagent_name in local_agent_config.get("subAgents", []):
        subagent_id = api_client.get_agent_by_short_name(target_project_id, subagent_name).get("id")
        subagent_list.append({"agentId": subagent_id})
    local_agent_config["subAgents"] = subagent_list

    tool_list = []
    for tool_name in local_agent_config.get("tools", []):
        tool_id = api_client.get_tool_by_short_name(target_project_id, tool_name).get("id")
        tool_list.append({"toolId": tool_id})
    local_agent_config["tools"] = tool_list    

    if local_agent_config.get("tracingConfigId"):
        datasource_id = api_client.get_datasource_by_short_name(target_project_id, local_agent_config.get("tracingConfigId")).get("id")
        local_agent_config["tracingConfigId"] = datasource_id
    return local_agent_config


def _normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize configuration for comparison."""
    # Remove fields that shouldn't be compared
    normalized = config.copy()
    fields_to_remove = ["id", "createdAt", "updatedAt", "publicId"]
    for field in fields_to_remove:
        normalized.pop(field, None)
    return normalized


def push_agent_operation(agent_name: str, project: Optional[str], profile: Optional[str], force: bool) -> None:
    """Push a local agent to the Canvas platform."""
    # Validate we're in a Canvas workspace
    require_canvas_workspace()
    
    try:
        # Get profile and create API client
        config_manager = ConfigManager()
        user_profile = config_manager.get_profile(profile)
        
        if not user_profile:
            console.print("[red]No authentication profile found. Run 'canvas login' first.[/red]")
            raise click.Abort()
        
        api_client = APIClient(user_profile)
        default_project = config_manager.get_default_project()

        # Determine target project
        target_project = project or default_project
        target_project_id = _resolve_project_id(target_project)
        if not target_project_id:
            console.print(f"[red]Project '{target_project}' not found. Run 'canvas add project {target_project}' first.[/red]")
            raise click.Abort()

        # Determine environment
        from ..operations.pull_agent import _get_project_environment
        environment = _get_project_environment(target_project)
        
        console.print(f"[blue]Preparing to push agent '{agent_name}' to project '{target_project}'[/blue]")
                
        # Step 1: Collect all dependencies
        console.print("[blue]Analyzing dependencies...[/blue]")
        
        all_agent_names, all_tool_names, all_datasource_names = collect_local_dependencies(agent_name)
        
        console.print(f"[green]✓[/green] Found {len(all_agent_names)} agents, {len(all_tool_names)} tools, {len(all_datasource_names)} datasources")
        
        # Step 2: Validate environment variables
        console.print("[blue]Validating environment variables...[/blue]")
        
        all_vars_present, missing_vars = validate_environment_variables(
            all_agent_names, all_tool_names, all_datasource_names, environment, api_client
        )
        
        if not all_vars_present:
            console.print(f"[yellow]Warning: Found {len(missing_vars)} missing environment variables:[/yellow]")
            for var in missing_vars:
                console.print(f"  • {var}")
            console.print(f"\n[blue]Please update env/{environment}.yaml with the missing variables.[/blue]")
            
            if not force and not click.confirm("Continue pushing with missing environment variables?", default=False):
                raise click.Abort()
        else:
            console.print("[green]✓[/green] All environment variables present")
        
        # Step 3: Push resources in dependency order
        console.print("[blue]Pushing resources...[/blue]")
        
        push_resources_optimized(
            all_agent_names, all_tool_names, all_datasource_names,
            target_project_id, api_client, environment, force
        )

        console.print(f"\n[green]✓[/green] Agent '{agent_name}' pushed successfully to project '{target_project}'!")
                
    except ValidationError as e:
        console.print(f"[red]Validation Error:[/red] {e}")
        raise click.Abort()
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}")
        raise click.Abort()
    except FileSystemError as e:
        console.print(f"[red]File Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


def collect_local_dependencies(agent_name: str) -> Tuple[List[str], List[str], List[str]]:
    """Collect all local dependencies (agents, tools, datasources) recursively."""
    all_agent_names = set()
    all_tool_names = set()
    all_datasource_names = set()
    
    def _collect_agent_dependencies(agent_name: str):
        if agent_name in all_agent_names:
            return  # Already processed
        
        agent_dir = Path("agents") / agent_name
        if not agent_dir.exists():
            console.print(f"[yellow]Warning:[/yellow] Agent directory not found: {agent_dir}")
            return
        
        all_agent_names.add(agent_name)
        
        # Load agent config
        try:
            agent_config = _load_agent_config(agent_dir, agent_name)
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not load agent config for {agent_name}: {e}")
            return
        
        # Collect subagents
        subagent_names = agent_config.get("subAgents", [])
        for subagent_name in subagent_names:
            _collect_agent_dependencies(subagent_name)
        
        # Collect tools
        tool_names = agent_config.get("tools", [])
        all_tool_names.update(tool_names)
        
        # Collect datasources from agent
        ds_name = agent_config.get("tracingConfigId", "")
        if ds_name:
            all_datasource_names.add(ds_name)
    
    # Start collection from root agent
    _collect_agent_dependencies(agent_name)
    
    # Also collect datasources from tools
    for tool_name in list(all_tool_names):
        tool_dir = Path("tools") / tool_name
        if tool_dir.exists():
            try:
                tool_file = tool_dir / "tool.yaml"
                if tool_file.exists():
                    with open(tool_file, 'r') as f:
                        tool_data = yaml.safe_load(f) or {}
                    
                    # Collect from tracingConfigId
                    ds_name = tool_data.get("tracingConfigId", "")
                    if ds_name:
                        all_datasource_names.add(ds_name)
                    
                    # Collect datasources from tool config fields
                    config = tool_data.get("config", {})
                    ds_name = config.get("dataSourceId", "")
                    if ds_name:
                        all_datasource_names.add(ds_name)
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not load tool config for {tool_name}: {e}")
    
    
    return list(all_agent_names), list(all_tool_names), list(all_datasource_names)


def validate_environment_variables(agent_names: List[str], tool_names: List[str], datasource_names: List[str], environment: str, api_client: Optional[APIClient] = None) -> Tuple[bool, List[str]]:
    """Validate that all required environment variables are present."""
    # Load environment variables
    from ..operations.pull_agent import load_env_variables_from_yaml
    env_vars = load_env_variables_from_yaml(environment)
    
    missing_vars = []
    
    # Fetch templates for better validation if API client is available
    tool_templates_map = {}
    datasource_templates_map = {}
    
    if api_client:
        try:
            tool_templates = api_client.list_tool_templates()
            for template in tool_templates:
                template_type = template.get("type")
                if template_type:
                    tool_templates_map[template_type] = template
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not fetch tool templates: {e}")
        
        try:
            datasource_templates = api_client.list_datasource_templates()
            for template in datasource_templates:
                template_type = template.get("type")
                if template_type:
                    datasource_templates_map[template_type] = template
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not fetch datasource templates: {e}")
    
    # Check agents
    for agent_name in agent_names:
        agent_dir = Path("agents") / agent_name
        if agent_dir.exists():
            try:
                agent_config = _load_agent_config(agent_dir, agent_name)
                missing_vars.extend(_find_missing_env_vars(agent_config, env_vars, f"agent {agent_name}"))
            except Exception:
                pass
    
    # Check tools with template-based validation
    for tool_name in tool_names:
        tool_file = Path("tools") / tool_name / "tool.yaml"
        if tool_file.exists():
            try:
                with open(tool_file, 'r') as f:
                    tool_data = yaml.safe_load(f) or {}
                
                # Use template-based validation if available
                tool_template_id = tool_data.get("type")
                if tool_template_id and tool_template_id in tool_templates_map:
                    template = tool_templates_map[tool_template_id]
                    missing_vars.extend(_validate_template_env_vars(tool_data, template, env_vars, f"tool {tool_name}"))
                else:
                    # Fallback to generic validation
                    missing_vars.extend(_find_missing_env_vars(tool_data, env_vars, f"tool {tool_name}"))
            except Exception:
                pass
    
    # Check datasources with template-based validation
    for ds_name in datasource_names:
        ds_file = Path("datasources") / ds_name / "datasource.yaml"
        if ds_file.exists():
            try:
                with open(ds_file, 'r') as f:
                    ds_data = yaml.safe_load(f) or {}
                
                # Use template-based validation if available
                ds_template_id = ds_data.get("type")
                if ds_template_id and ds_template_id in datasource_templates_map:
                    template = datasource_templates_map[ds_template_id]
                    missing_vars.extend(_validate_template_env_vars(ds_data, template, env_vars, f"datasource {ds_name}"))
                else:
                    # Fallback to generic validation
                    missing_vars.extend(_find_missing_env_vars(ds_data, env_vars, f"datasource {ds_name}"))
            except Exception:
                pass
    
    return len(missing_vars) == 0, missing_vars


def _validate_template_env_vars(data: Dict[str, Any], template: Dict[str, Any], env_vars: Dict[str, Any], resource_name: str) -> List[str]:
    """Validate environment variables based on template schema."""
    missing = []
    
    if not template or "configSchema" not in template:
        # Fallback to generic validation
        return _find_missing_env_vars(data, env_vars, resource_name)
    
    config = data.get("config", {})
    
    # Check environment-specific fields based on template
    for field_schema in template["configSchema"]:
        field_name = field_schema.get("fieldName")
        is_env_specific = field_schema.get("isEnvSpecific")
        
        if field_name and is_env_specific and field_name in config:
            field_value = config[field_name]
            
            # Check if it's an environment variable reference
            if isinstance(field_value, str) and field_value.startswith("${") and field_value.endswith("}"):
                env_var = field_value[2:-1]  # Remove ${ and }
                if env_var not in env_vars:
                    missing.append(f"{env_var} (required by {resource_name} field '{field_name}')")
            else:
                # If it's not an env var reference, check if the expected env var exists
                # This handles cases where the field should be an env var but isn't
                from ..operations.pull_resources import _convert_field_name_to_env_var
                resource_env_name = _convert_field_name_to_env_var(resource_name)
                field_env_name = _convert_field_name_to_env_var(field_name)
                expected_env_var = f"{resource_env_name}_{field_env_name}"
                
                if expected_env_var not in env_vars:
                    missing.append(f"{expected_env_var} (expected for {resource_name} field '{field_name}')")
    
    # Also check for any other ${VAR} references in the data
    missing.extend(_find_missing_env_vars(data, env_vars, resource_name))
    
    return missing


def _find_missing_env_vars(data: Dict[str, Any], env_vars: Dict[str, Any], resource_name: str) -> List[str]:
    """Find missing environment variables in data."""
    missing = []
    
    def check_value(value, path=""):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]  # Remove ${ and }
            if env_var not in env_vars:
                missing.append(f"{env_var} (required by {resource_name})")
        elif isinstance(value, dict):
            for k, v in value.items():
                check_value(v, f"{path}.{k}" if path else k)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                check_value(item, f"{path}[{i}]" if path else f"[{i}]")
    
    check_value(data)
    return missing


def push_resources_optimized(
    agent_names: List[str], 
    tool_names: List[str], 
    datasource_names: List[str],
    target_project_id: str, 
    api_client: APIClient, 
    environment: str,
    force: bool
) -> None:
    """Push all resources efficiently in dependency order."""
    from ..operations.pull_agent import load_env_variables_from_yaml
    env_vars = load_env_variables_from_yaml(environment)
    
    # Fetch all tool templates once for efficient lookups
    tool_templates_map = {}
    try:
        tool_templates = api_client.list_tool_templates()
        for template in tool_templates:
            template_type = template.get("type")
            if template_type:
                tool_templates_map[template_type] = template
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not fetch tool templates: {e}")
    
    # Push datasources first (no dependencies)
    for ds_name in datasource_names:
        _push_datasource(ds_name, target_project_id, api_client, env_vars, force)
    
    # Push tools second (depend on datasources)
    for tool_name in tool_names:
        _push_tool(tool_name, target_project_id, api_client, env_vars, tool_templates_map, force)
    
    # Push agents last (depend on tools and datasources)
    # Build dependency map for correct order
    agent_dependencies = {}
    
    for agent_name in agent_names:
        agent_dir = Path("agents") / agent_name
        if agent_dir.exists():
            try:
                agent_config = _load_agent_config(agent_dir, agent_name)
                subagent_names = agent_config.get("subAgents", [])
                agent_dependencies[agent_name] = subagent_names
            except Exception:
                agent_dependencies[agent_name] = []
        else:
            agent_dependencies[agent_name] = []
    
    # Process agents in dependency order (children first)
    processed_agents = set()
    
    def _process_agent(agent_name: str):
        if agent_name in processed_agents or agent_name not in agent_names:
            return
        
        # Process dependencies first
        for dep_name in agent_dependencies.get(agent_name, []):
            _process_agent(dep_name)
        
        _push_agent_optimized(agent_name, target_project_id, api_client, env_vars, force)
        processed_agents.add(agent_name)
    
    # Process all agents
    for agent_name in agent_names:
        _process_agent(agent_name)


def _push_datasource(ds_name: str, target_project_id: str, api_client: APIClient, env_vars: Dict[str, Any], force: bool) -> None:
    """Push a datasource to the platform."""
    ds_file = Path("datasources") / ds_name / "datasource.yaml"
    if not ds_file.exists():
        console.print(f"[yellow]Warning:[/yellow] Datasource file not found: {ds_file}")
        return
    
    try:
        with open(ds_file, 'r') as f:
            ds_data = yaml.safe_load(f) or {}
        
        # Resolve environment variables
        resolved_ds_data = _resolve_env_vars(ds_data, env_vars)
        
        # Check if datasource exists
        existing_ds = None
        try:
            existing_ds = api_client.get_datasource_by_short_name(target_project_id, ds_name)
        except APIError:
            # Datasource doesn't exist, we'll create it
            existing_ds = None
        
        if existing_ds:
            # Update existing
            try:
                api_client.update_datasource(target_project_id, existing_ds.get("id"), resolved_ds_data)
                console.print(f"[green]✓[/green] Updated datasource: {ds_name}")
            except APIError as e:
                console.print(f"[red]Error updating datasource {ds_name}:[/red] {e}")
        else:
            # Create new
            try:
                api_client.create_datasource(target_project_id, resolved_ds_data, ds_name)
                console.print(f"[green]✓[/green] Created datasource: {ds_name}")
            except APIError as e:
                console.print(f"[red]Error creating datasource {ds_name}:[/red] {e}")
    
    except Exception as e:
        console.print(f"[red]Error pushing datasource {ds_name}:[/red] {e}")


def _push_tool(tool_name: str, target_project_id: str, api_client: APIClient, env_vars: Dict[str, Any], tool_templates_map: Dict[str, Any], force: bool) -> None:
    """Push a tool to the platform."""
    tool_file = Path("tools") / tool_name / "tool.yaml"
    tool_query_file = Path("tools") / tool_name / "query.txt"
    tool_example_input_file = Path("tools") / tool_name / "example_input.txt"
    if not tool_file.exists():
        console.print(f"[yellow]Warning:[/yellow] Tool file not found: {tool_file}")
        return
    
    try:
        with open(tool_file, 'r') as f:
            tool_data = yaml.safe_load(f) or {}
        
        
        # Convert datasource short names back to IDs based on template schema
        tool_template_id = tool_data.get("type")
        if tool_template_id and tool_template_id in tool_templates_map:
            tool_template = tool_templates_map[tool_template_id]
            if "configSchema" in tool_template:
                config = tool_data.get("config", {})
                # Find fields with dataType "DataSource" in the template and convert short names to IDs
                for field_schema in tool_template["configSchema"]:
                    if field_schema.get("dataType") == "DataSource":
                        field_name = field_schema.get("fieldName")
                        if field_name and field_name in config:
                            ds_short_name = config[field_name]
                            if ds_short_name:
                                # Find the datasource ID by short name
                                try:
                                    ds_obj = api_client.get_datasource_by_short_name(target_project_id, ds_short_name)
                                    if ds_obj:
                                        config[field_name] = ds_obj.get("id")
                                    else:
                                        console.print(f"[yellow]Warning:[/yellow] Datasource '{ds_short_name}' not found for tool '{tool_name}' - keeping short name")
                                except APIError:
                                    console.print(f"[yellow]Warning:[/yellow] Datasource '{ds_short_name}' not found for tool '{tool_name}' - keeping short name")
                tool_data["config"] = config
        if tool_query_file.exists():
            with open(tool_query_file, 'r') as f:
                tool_data["config"]["query"] = f.read()
        if tool_example_input_file.exists():
            with open(tool_example_input_file, 'r') as f:
                tool_data["config"]["exampleInput"] = f.read()
        
        # Resolve environment variables
        resolved_tool_data = _resolve_env_vars(tool_data, env_vars)
        
        # Check if tool exists
        existing_tool = None
        try:
            existing_tool = api_client.get_tool_by_short_name(target_project_id, tool_name)
        except APIError:
            # Tool doesn't exist, we'll create it
            existing_tool = None
        
        if existing_tool:
            # Update existing
            try:
                api_client.update_tool(target_project_id, existing_tool.get("id"), resolved_tool_data)
                console.print(f"[green]✓[/green] Updated tool: {tool_name}")
            except APIError as e:
                console.print(f"[red]Error updating tool {tool_name}:[/red] {e}")
        else:
            # Create new
            try:
                api_client.create_tool(target_project_id, resolved_tool_data, tool_name)
                console.print(f"[green]✓[/green] Created tool: {tool_name}")
            except APIError as e:
                console.print(f"[red]Error creating tool {tool_name}:[/red] {e}")
    
    except Exception as e:
        console.print(f"[red]Error pushing tool {tool_name}:[/red] {e}")


def _push_agent_optimized(agent_name: str, target_project_id: str, api_client: APIClient, env_vars: Dict[str, Any], force: bool) -> None:
    """Push an agent to the platform."""
    agent_dir = Path("agents") / agent_name
    if not agent_dir.exists():
        console.print(f"[yellow]Warning:[/yellow] Agent directory not found: {agent_dir}")
        return
    
    try:
        # Load agent config
        agent_config = _load_agent_config(agent_dir, agent_name)
        
        # Validate agent configuration
        _validate_agent_config(agent_config, force)
        
        # Resolve references (convert short names to IDs)
        resolved_config = _resolve_references(agent_config, api_client, target_project_id)
        
        # Check if agent exists
        existing_agent = None
        try:
            existing_agent = api_client.get_agent_by_short_name(target_project_id, agent_name)
        except APIError:
            # Agent doesn't exist, we'll create it
            existing_agent = None
        
        if existing_agent:
            # Update existing
            try:
                if _normalize_config(existing_agent) != _normalize_config(resolved_config):
                    api_client.update_agent(target_project_id, existing_agent.get("id"), resolved_config)
                    console.print(f"[green]✓[/green] Updated agent: {agent_name}")
                else:
                    console.print(f"[blue]•[/blue] Agent {agent_name} is up to date")
            except APIError as e:
                console.print(f"[red]Error updating agent {agent_name}:[/red] {e}")
        else:
            # Create new
            try:
                api_client.create_agent(target_project_id, resolved_config, agent_name)
                console.print(f"[green]✓[/green] Created agent: {agent_name}")
            except APIError as e:
                console.print(f"[red]Error creating agent {agent_name}:[/red] {e}")
    
    except Exception as e:
        console.print(f"[red]Error pushing agent {agent_name}:[/red] {e}")


def _resolve_env_vars(data: Dict[str, Any], env_vars: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve environment variables in data."""
    def resolve_value(value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]  # Remove ${ and }
            if env_var in env_vars:
                return env_vars[env_var]
            else:
                # Keep the placeholder if not found
                return value
        elif isinstance(value, dict):
            return {k: resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [resolve_value(item) for item in value]
        return value
    
    return resolve_value(data)


def _push_agent(target_project_id: str, agent: str, api_client: APIClient, force: bool) -> None:
    """Push a local agent to the Canvas platform."""
    local_agent_config = _load_agent_config(Path("agents") / agent , agent)
    tool_names = local_agent_config.get("tools", [])
    print("tool_names:", tool_names)
    datasource_name = local_agent_config.get("tracingConfigId", "")
    print("datasource_name:", datasource_name)
    subagent_names = local_agent_config.get("subAgents", [])
    print("subagent_names:", subagent_names)
    
    # Validate agent configuration
    _validate_agent_config(local_agent_config, force)

    # Subagents
    for subagent_name in subagent_names:
        _push_agent(target_project_id, subagent_name, api_client, force)
    
    # Tools and datasources are pushed automatically as dependencies
    # No individual push operations needed
    if tool_names:
        console.print(f"[blue]Agent references {len(tool_names)} tools - they will be resolved automatically[/blue]")
    if datasource_name:
        console.print(f"[blue]Agent references datasource '{datasource_name}' - it will be resolved automatically[/blue]")

    remote_agent_config = None
    try:
        remote_agent_config_id = api_client.get_agent_by_short_name(target_project_id, agent).get("id")
        remote_agent_config = pull_agents([remote_agent_config_id], target_project_id, api_client, write_to_file=False)[1][0]
    except APIError:
        print("remote agent not found in the target project")
        remote_agent_config = None
    except Exception as e:
        print(f"error getting remote agent: {e}")
        remote_agent_config = None

    if remote_agent_config is None:
        if local_agent_config is None:
            console.print(f"[yellow]•[/yellow] Skipping agent {agent}: no local config and not found remotely")
            return
        local_agent_config = _resolve_references(local_agent_config, api_client, target_project_id)
        api_client.create_agent(target_project_id, local_agent_config, agent)
        console.print(f"[green]✓[/green] Created agent {agent} in project {target_project_id}")
    else:
        if _normalize_config(remote_agent_config) != _normalize_config(local_agent_config):
            local_agent_config = _resolve_references(local_agent_config, api_client, target_project_id)
            api_client.update_agent(target_project_id, remote_agent_config_id, local_agent_config)
            console.print(f"[green]✓[/green] Updated agent {agent} in project {target_project_id}")
