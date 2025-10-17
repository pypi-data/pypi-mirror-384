"""Shared resource pulling functions for Canvas CLI operations."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from rich.console import Console

from ..utils.exceptions import APIError, FileSystemError
from ..services.api_client import APIClient
from ..utils.helpers import convert_tool_obj_to_tool_data, convert_datasource_obj_to_datasource_data, convert_agent_obj_to_agent_data

console = Console()


def collect_all_dependencies(agent_ids: List[str], project_id: str, api_client: APIClient) -> Tuple[List[str], List[str], List[str]]:
    """Collect all unique dependencies (agents, tools, datasources) recursively without pulling them."""
    all_agent_ids = set()
    all_tool_ids = set()
    all_datasource_ids = set()
    
    # Fetch all tool templates once for efficient lookups
    tool_templates_map = {}
    try:
        tool_templates = api_client.list_tool_templates()
        for template in tool_templates:
            template_type = template.get("type")
            if template_type:
                tool_templates_map[template_type] = template
    except Exception:
        pass  # Continue without templates if fetch fails
    
    def _collect_agent_dependencies(agent_id: str, depth: int = 0):
        if agent_id in all_agent_ids:
            return  # Already processed
        
        if depth > 10:  # Prevent infinite recursion
            console.print(f"[yellow]Warning:[/yellow] Maximum recursion depth reached for agent {agent_id}")
            return
        
        all_agent_ids.add(agent_id)
        
        # Get agent data
        agent_obj = _safe_get_agent(api_client, project_id, agent_id)
        if not agent_obj:
            return
        
        agent_data = convert_agent_obj_to_agent_data(agent_obj)
        
        # Collect subagents
        subagent_ids = _extract_subagent_ids(agent_data.get("subAgents", []))
        for subagent_id in subagent_ids:
            _collect_agent_dependencies(subagent_id, depth + 1)
        
        # Collect tools
        tool_ids = _extract_tool_ids(agent_data.get("tools", []))
        all_tool_ids.update(tool_ids)
        
        # Collect datasources from agent
        ds_id = agent_data.get("tracingConfigId", "")
        if ds_id:
            all_datasource_ids.add(ds_id)
    
    # Start collection from root agents
    for agent_id in agent_ids:
        _collect_agent_dependencies(agent_id)
    
    # Also collect datasources from tools
    for tool_id in list(all_tool_ids):
        tool_obj = _safe_get_tool(api_client, project_id, tool_id)
        if tool_obj:
            tool_data = convert_tool_obj_to_tool_data(tool_obj)
            # Check tracingConfigId at tool level
            ds_id = tool_data.get("tracingConfigId", "")
            if ds_id:
                all_datasource_ids.add(ds_id)
            
            # Get tool template to identify DataSource fields
            tool_template_id = tool_data.get("type")
            if tool_template_id and tool_template_id in tool_templates_map:
                tool_template = tool_templates_map[tool_template_id]
                if "configSchema" in tool_template:
                    config = tool_data.get("config", {})
                    # Find fields with dataType "DataSource" in the template
                    for field_schema in tool_template["configSchema"]:
                        if field_schema.get("dataType") == "DataSource":
                            field_name = field_schema.get("fieldName")
                            if field_name and field_name in config:
                                ds_id_from_field = config[field_name]
                                if ds_id_from_field:
                                    all_datasource_ids.add(ds_id_from_field)
    return list(all_agent_ids), list(all_tool_ids), list(all_datasource_ids)


def pull_resources_optimized(
    agent_ids: List[str], 
    tool_ids: List[str], 
    datasource_ids: List[str],
    project_id: str, 
    api_client: APIClient, 
    existing_env_vars: Dict[str, Any],
    agents_dir: Path, 
    tools_dir: Path, 
    datasources_dir: Path,
    environment: str
) -> Dict[str, Any]:
    """Pull all resources efficiently and extract environment variables."""
    new_env_vars = {}
    
    # Fetch all tool templates once and create a lookup map
    tool_templates_map = {}
    try:
        tool_templates = api_client.list_tool_templates()
        for template in tool_templates:
            template_type = template.get("type")
            if template_type:
                tool_templates_map[template_type] = template
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not fetch tool templates: {e}")
    
    # Fetch all datasource templates once and create a lookup map
    datasource_templates_map = {}
    try:
        datasource_templates = api_client.list_datasource_templates()
        for template in datasource_templates:
            template_type = template.get("type")
            if template_type:
                datasource_templates_map[template_type] = template
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not fetch datasource templates: {e}")
    
    # Pull datasources first (no dependencies)
    for ds_id in datasource_ids:
        ds_obj = _safe_get_datasource(api_client, project_id, ds_id)
        if ds_obj:
            ds_data = convert_datasource_obj_to_datasource_data(ds_obj)
            
            # Extract environment-specific fields based on template
            ds_template_id = ds_data.get("type")
            if ds_template_id and ds_template_id in datasource_templates_map:
                ds_template = datasource_templates_map[ds_template_id]
                ds_data, ds_env_specific_vars = _extract_env_specific_fields(
                    ds_data, ds_template, "datasource", ds_obj.get("shortName"), existing_env_vars
                )
                new_env_vars.update(ds_env_specific_vars)
            
            # Extract remaining environment variables (for existing ${VAR} references)
            ds_env_vars = _extract_env_variables(ds_data, existing_env_vars, new_env_vars)
            new_env_vars.update(ds_env_vars)
            
            # Save datasource
            ds_dir = datasources_dir / ds_obj.get("shortName")
            ds_dir.mkdir(parents=True, exist_ok=True)
            _write_yaml(ds_dir / "datasource.yaml", ds_data)
            console.print(f"[green]✓[/green] Saved datasource: {ds_dir}/datasource.yaml")
    
    # Pull tools second (depend on datasources)
    for tool_id in tool_ids:
        tool_obj = _safe_get_tool(api_client, project_id, tool_id)
        if tool_obj:
            tool_data = convert_tool_obj_to_tool_data(tool_obj)
            
            # Replace datasource IDs with short names based on template schema
            tool_template_id = tool_data.get("type")
            if tool_template_id and tool_template_id in tool_templates_map:
                tool_template = tool_templates_map[tool_template_id]
                if "configSchema" in tool_template:
                    config = tool_data.get("config", {})
                    # Find fields with dataType "DataSource" in the template and replace IDs with short names
                    for field_schema in tool_template["configSchema"]:
                        if field_schema.get("dataType") == "DataSource":
                            field_name = field_schema.get("fieldName")
                            if field_name and field_name in config:
                                ds_id = config[field_name]
                                if ds_id:
                                    ds_obj = _safe_get_datasource(api_client, project_id, ds_id)
                                    if ds_obj:
                                        config[field_name] = ds_obj.get("shortName")
                    tool_data["config"] = config
                
                # Extract environment-specific fields based on template
                tool_data, tool_env_specific_vars = _extract_env_specific_fields(
                    tool_data, tool_template, "tool", tool_obj.get("shortName"), existing_env_vars
                )
                new_env_vars.update(tool_env_specific_vars)
            
            # Extract remaining environment variables (for existing ${VAR} references)
            tool_env_vars = _extract_env_variables(tool_data, existing_env_vars, new_env_vars)
            new_env_vars.update(tool_env_vars)
            
            # Save tool
            tool_dir = tools_dir / tool_obj.get("shortName")
            tool_dir.mkdir(parents=True, exist_ok=True)
            if(tool_data.get("config",{}).get("query")):
                with open(tool_dir / "query.txt", 'w', encoding='utf-8') as f:
                    f.write(tool_data["config"]["query"])
                tool_data["config"]["query"] = "@query.txt"
            if(tool_data.get("config",{}).get("exampleInput")):
                with open(tool_dir / "example_input.txt", 'w', encoding='utf-8') as f:
                    f.write(tool_data["config"]["exampleInput"])
                tool_data["config"]["exampleInput"] = "@example_input.txt"
            _write_yaml(tool_dir / "tool.yaml", tool_data)
            console.print(f"[green]✓[/green] Saved tool: {tool_dir}/tool.yaml")
    
    # Pull agents last (depend on tools and datasources)
    # Build dependency map for correct order
    agent_dependencies = {}
    agent_objects = {}
    
    for agent_id in agent_ids:
        agent_obj = _safe_get_agent(api_client, project_id, agent_id)
        if agent_obj:
            agent_objects[agent_id] = agent_obj
            agent_data = convert_agent_obj_to_agent_data(agent_obj)
            subagent_ids = _extract_subagent_ids(agent_data.get("subAgents", []))
            agent_dependencies[agent_id] = subagent_ids
    
    # Process agents in dependency order (children first)
    processed_agents = set()
    
    def _process_agent(agent_id: str):
        if agent_id in processed_agents or agent_id not in agent_objects:
            return
        
        # Process dependencies first
        for dep_id in agent_dependencies.get(agent_id, []):
            _process_agent(dep_id)
        
        agent_obj = agent_objects[agent_id]
        agent_data = convert_agent_obj_to_agent_data(agent_obj)
        
        # Update references to use short names
        subagent_ids = _extract_subagent_ids(agent_data.get("subAgents", []))
        agent_data["subAgents"] = [agent_objects[sid].get("shortName") for sid in subagent_ids if sid in agent_objects]
        
        tool_ids_for_agent = _extract_tool_ids(agent_data.get("tools", []))
        tool_short_names = []
        for tid in tool_ids_for_agent:
            tool_obj = _safe_get_tool(api_client, project_id, tid)
            if tool_obj:
                tool_short_names.append(tool_obj.get("shortName"))
        agent_data["tools"] = tool_short_names
        
        ds_id = agent_data.get("tracingConfigId", "")
        if ds_id:
            ds_obj = _safe_get_datasource(api_client, project_id, ds_id)
            if ds_obj:
                agent_data["tracingConfigId"] = ds_obj.get("shortName")
        
        # Save agent
        agent_dir = agents_dir / agent_obj.get("shortName")
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract system prompt to separate file
        system_prompt = agent_data.get("promptConfig", {}).get("systemPrompt", "")
        if system_prompt:
            agent_data_without_prompt = agent_data.copy()
            agent_data_without_prompt["promptConfig"]["systemPrompt"] = "@system_prompt.txt"
            
            with open(agent_dir / "system_prompt.txt", 'w', encoding='utf-8') as f:
                f.write(system_prompt)
            
            _write_yaml(agent_dir / "agent.yaml", agent_data_without_prompt)
        else:
            _write_yaml(agent_dir / "agent.yaml", agent_data)
        
        console.print(f"[green]✓[/green] Saved agent: {agent_dir}/agent.yaml")
        processed_agents.add(agent_id)
    
    # Process all agents
    for agent_id in agent_ids:
        _process_agent(agent_id)
    
    return new_env_vars


def _safe_get_agent(api_client: APIClient, project_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
    """Safely get agent, return None if not found."""
    try:
        return api_client.get_agent(project_id, agent_id)
    except APIError:
        return None


def _safe_get_tool(api_client: APIClient, project_id: str, tool_id: str) -> Optional[Dict[str, Any]]:
    """Safely get tool, return None if not found."""
    try:
        return api_client.get_tool(project_id, tool_id)
    except APIError:
        return None


def _safe_get_datasource(api_client: APIClient, project_id: str, datasource_id: str) -> Optional[Dict[str, Any]]:
    """Safely get datasource, return None if not found."""
    try:
        return api_client.get_datasource(project_id, datasource_id)
    except APIError:
        return None


def _extract_subagent_ids(subagents: List[Dict[str, Any]]) -> List[str]:
    """Extract a list of agent ids from a list of subagents."""
    subagent_ids = []
    for subagent in subagents:
        subagent_ids.append(subagent.get("agentId"))
    return subagent_ids


def _extract_tool_ids(tools: List[Dict[str, Any]]) -> List[str]:
    """Extract a list of tool ids from a list of tools."""
    tool_ids = []
    for tool in tools:
        tool_ids.append(tool.get("toolId"))
    return tool_ids


def _resolve_protected_references(data: Dict[str, Any], existing_env_vars: Optional[Dict[str, Any]] = None, environment: Optional[str] = None) -> Dict[str, Any]:
    """Resolve protected references in configuration data."""
    if existing_env_vars is None:
        existing_env_vars = {}
    
    # Load environment variables from YAML if environment is specified
    if environment:
        from .pull_agent import load_env_variables_from_yaml
        env_vars = load_env_variables_from_yaml(environment)
        # Merge with existing env vars, prioritizing YAML values
        merged_env_vars = existing_env_vars.copy()
        merged_env_vars.update(env_vars)
        existing_env_vars = merged_env_vars

    def resolve_value(value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]  # Remove ${ and }
            if env_var in existing_env_vars:
                resolved_value = existing_env_vars[env_var]
                existing_env_vars[env_var] = resolved_value
                return resolved_value
            elif env_var in os.environ:
                resolved_value = os.environ[env_var]
                existing_env_vars[env_var] = resolved_value
                return resolved_value
            else:
                # Keep the placeholder and add to env vars for later resolution
                existing_env_vars[env_var] = f"# TODO: Set {env_var} for {type}"
                return value
        elif isinstance(value, dict):
            return {k: resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [resolve_value(item) for item in value]
        return value

    return resolve_value(data)


def _extract_env_variables(data: Dict[str, Any], existing_env_vars: Dict[str, Any], new_env_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract environment variables from data without resolving them."""
    if new_env_vars is None:
        new_env_vars = {}
    
    additional_env_vars = {}
    
    def extract_from_value(value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]  # Remove ${ and }
            # Only add placeholder if the variable doesn't exist in existing_env_vars or new_env_vars
            if env_var not in existing_env_vars and env_var not in new_env_vars and env_var not in additional_env_vars:
                additional_env_vars[env_var] = f"# TODO: Set {env_var}"
        elif isinstance(value, dict):
            for v in value.values():
                extract_from_value(v)
        elif isinstance(value, list):
            for item in value:
                extract_from_value(item)
    
    extract_from_value(data)
    return additional_env_vars


def _convert_field_name_to_env_var(field_name: str) -> str:
    """Convert field name to environment variable format (uppercase with underscores)."""
    import re
    # Replace spaces and hyphens with underscores first
    s0 = re.sub(r'[\s\-]+', '_', field_name)
    # Insert underscore before uppercase letters that follow lowercase letters
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s0)
    # Insert underscore before uppercase letters that follow lowercase letters or digits
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    # Clean up multiple underscores
    s3 = re.sub('_+', '_', s2)
    # Remove leading/trailing underscores
    s4 = s3.strip('_')
    return s4.upper()


def _extract_env_specific_fields(
    data: Dict[str, Any], 
    template: Dict[str, Any], 
    resource_type: str,
    resource_name: str,
    existing_env_vars: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Extract environment-specific fields from data based on template schema.
    
    Returns:
        Tuple of (modified_data_with_env_refs, new_env_vars)
    """
    if not template or "configSchema" not in template:
        return data, {}
    
    modified_data = data.copy()
    new_env_vars = {}
    config = modified_data.get("config", {})
    modified_config = config.copy()
    
    for field_schema in template["configSchema"]:
        field_name = field_schema.get("fieldName")
        is_env_specific = field_schema.get("isEnvSpecific")
        is_protected = field_schema.get("isProtected")
        if(field_name and is_protected and field_name in config):
            resource_env_name = _convert_field_name_to_env_var(resource_name)
            field_env_name = _convert_field_name_to_env_var(field_name)
            env_var_name = f"{resource_env_name}_{field_env_name}"
            modified_config[field_name] = f"${{{env_var_name}}}"
            if(env_var_name not in existing_env_vars):
                new_env_vars[env_var_name] = {
                    "isProtected": True,
                    "value": config[field_name]
                }
            console.print(f"[blue]•[/blue] Extracted protected {resource_type} '{resource_name}' field '{field_name}' to environment variable '{env_var_name}'")
        
        elif(field_name and is_env_specific and field_name in config):
            field_value = config[field_name]
            
            # Skip if value is already an environment variable reference
            if isinstance(field_value, str) and field_value.startswith("${") and field_value.endswith("}"):
                continue
            
            # Convert resource name and field name to environment variable name
            resource_env_name = _convert_field_name_to_env_var(resource_name)
            field_env_name = _convert_field_name_to_env_var(field_name)
            env_var_name = f"{resource_env_name}_{field_env_name}"
            
            # Create environment variable reference
            env_ref = f"${{{env_var_name}}}"
            
            # Update the config with environment variable reference
            modified_config[field_name] = env_ref
            
            # Add to new environment variables if not already present (write actual value, not placeholder)
            if env_var_name not in existing_env_vars:
                new_env_vars[env_var_name] = field_value
                console.print(f"[blue]•[/blue] Extracted {resource_type} '{resource_name}' field '{field_name}' to environment variable '{env_var_name}'")
    
    # Update the modified data with the new config
    if modified_config != config:
        modified_data["config"] = modified_config
    
    return modified_data, new_env_vars


def _write_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Write data to YAML file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
    except Exception as e:
        raise FileSystemError(f"Failed to write file {path}: {e}")


def pull_agents(agent_ids: List[str], project_id: str, api_client: APIClient, write_to_file: bool = True, existing_env_vars: Optional[Dict[str, Any]] = None, agents_dir: Optional[Path] = None, tools_dir: Optional[Path] = None, datasources_dir: Optional[Path] = None, environment: Optional[str] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Pull agents and their dependencies."""
    # Set default directories if not provided
    if agents_dir is None:
        agents_dir = Path("agents")
    if tools_dir is None:
        tools_dir = Path("tools")
    if datasources_dir is None:
        datasources_dir = Path("datasources")
        
    agent_names = []
    agent_datas = []
    for agent_id in agent_ids:
        # Save agent.yaml
        agent_obj = _safe_get_agent(api_client, project_id, agent_id)
        if not agent_obj:
            console.print(f"[yellow]•[/yellow] Agent not found or inaccessible: {agent_id}")
            continue
        agent_data = convert_agent_obj_to_agent_data(agent_obj)

        # Pull required subagents
        subagent_ids = _extract_subagent_ids(agent_data.get("subAgents", []))
        print("subagent_ids:", subagent_ids)
        subagent_names, subagent_datas = pull_agents(subagent_ids, project_id, api_client, write_to_file=write_to_file, existing_env_vars=existing_env_vars, agents_dir=agents_dir, tools_dir=tools_dir, datasources_dir=datasources_dir, environment=environment)
        agent_data["subAgents"] = subagent_names
        # Pull required tools
        tool_ids = _extract_tool_ids(agent_data.get("tools", []))
        tool_short_names, tool_datas = pull_tools(tool_ids, project_id, api_client, write_to_file=write_to_file, existing_env_vars=existing_env_vars, tools_dir=tools_dir, datasources_dir=datasources_dir, environment=environment)
        agent_data["tools"] = tool_short_names
        # Pull required datasources
        ds_id = agent_data.get("tracingConfigId", "")
        if ds_id:
            ds_names, ds_datas = pull_datasources([ds_id], project_id, api_client, write_to_file=write_to_file, existing_env_vars=existing_env_vars, datasources_dir=datasources_dir, environment=environment)
            agent_data["tracingConfigId"] = ds_names[0]

        agent_names.append(agent_obj.get("shortName"))
        agent_datas.append(agent_data)
        if(write_to_file):
            agent_dir = agents_dir / agent_obj.get("shortName")
            agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract system prompt to separate file for better readability
            system_prompt = agent_data.get("systemPrompt", "")
            if system_prompt:
                # Remove system prompt from YAML and save to separate file
                agent_data_without_prompt = agent_data.copy()
                agent_data_without_prompt.pop("systemPrompt", None)
                
                # Save system prompt to text file
                with open(agent_dir / "system_prompt.txt", 'w', encoding='utf-8') as f:
                    f.write(system_prompt)
                console.print(f"[green]✓[/green] Saved system prompt: {agent_dir / 'system_prompt.txt'}")
                
                # Save agent.yaml without system prompt
                _write_yaml(agent_dir / "agent.yaml", agent_data_without_prompt)
            else:
                # No system prompt, save as is
                _write_yaml(agent_dir / "agent.yaml", agent_data)
            
            # Note: Removed config.yaml - publicId will be resolved dynamically
            console.print(f"[green]✓[/green] Saved agent: {agent_dir / 'agent.yaml'}")

    return agent_names, agent_datas


def pull_tools(tool_ids: List[str], project_id: str, api_client: APIClient, write_to_file: bool = True, existing_env_vars: Optional[Dict[str, Any]] = None, tools_dir: Optional[Path] = None, datasources_dir: Optional[Path] = None, environment: Optional[str] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Pull tools into tools directory."""
    # Set default directories if not provided
    if tools_dir is None:
        tools_dir = Path("tools")
    if datasources_dir is None:
        datasources_dir = Path("datasources")
    
    # Fetch tool templates for environment-specific field handling
    tool_templates_map = {}
    try:
        tool_templates = api_client.list_tool_templates()
        for template in tool_templates:
            template_type = template.get("type")
            if template_type:
                tool_templates_map[template_type] = template
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not fetch tool templates: {e}")
        
    tool_names = []
    tool_datas = []
    for tool_id in tool_ids:
        tool_obj = _safe_get_tool(api_client, project_id, tool_id)
        if not tool_obj:
            console.print(f"[yellow]•[/yellow] Tool not found or inaccessible: {tool_id}")
            continue
        tool_data = convert_tool_obj_to_tool_data(tool_obj)
        tool_short_name = tool_obj.get("shortName")

        # Pull required datasources
        if(tool_data.get("config",{}).get("dataSourceId")):
            ds_names, ds_datas = pull_datasources([tool_data.get("config",{}).get("dataSourceId")], project_id, api_client, write_to_file=write_to_file, existing_env_vars=existing_env_vars, datasources_dir=datasources_dir, environment=environment)
            if(len(ds_names) > 0):
                tool_data["config"]["dataSourceId"] = ds_names[0]
            else:
                console.print(f"[yellow]•[/yellow] Datasource not found or inaccessible: {tool_data.get('config',{}).get('dataSourceId')}. Resolve the datasource to pull the tool {tool_short_name} successfully.")
                continue
        
        # Extract environment-specific fields based on template
        tool_template_id = tool_data.get("type")
        if tool_template_id and tool_template_id in tool_templates_map:
            tool_template = tool_templates_map[tool_template_id]
            tool_data, tool_env_specific_vars = _extract_env_specific_fields(
                tool_data, tool_template, "tool", tool_short_name, existing_env_vars or {}
            )
            # Note: This function doesn't return new_env_vars, so we can't merge them here
            # The environment variables will be handled by the calling function
        
        tool_datas.append(tool_data)
        tool_names.append(tool_short_name)
        if(write_to_file):
            tool_dir = tools_dir / f"{tool_short_name}"
            tool_dir.mkdir(parents=True, exist_ok=True)
            _write_yaml(tool_dir / "tool.yaml", _resolve_protected_references(tool_data, existing_env_vars=existing_env_vars, environment=environment))
            # Note: Removed config.yaml - publicId will be resolved dynamically
            console.print(f"[green]✓[/green] Saved tool: {tool_dir / 'tool.yaml'}")

    return tool_names, tool_datas


def pull_datasources(datasource_ids: List[str], project_id: str, api_client: APIClient, write_to_file: bool = True, existing_env_vars: Optional[Dict[str, Any]] = None, datasources_dir: Optional[Path] = None, environment: Optional[str] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Pull datasources into datasources directory."""
    # Set default directories if not provided
    if datasources_dir is None:
        datasources_dir = Path("datasources")
    
    # Fetch datasource templates for environment-specific field handling
    datasource_templates_map = {}
    try:
        datasource_templates = api_client.list_datasource_templates()
        for template in datasource_templates:
            template_type = template.get("type")
            if template_type:
                datasource_templates_map[template_type] = template
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not fetch datasource templates: {e}")
        
    ds_names = []
    ds_datas = []
    for ds_id in datasource_ids:
        ds_obj = _safe_get_datasource(api_client, project_id, ds_id)
        if not ds_obj:
            console.print(f"[yellow]•[/yellow] Datasource not found or inaccessible: {ds_id}")
            continue
        ds_short_name = ds_obj.get("shortName")
        ds_data = convert_datasource_obj_to_datasource_data(ds_obj)
        
        # Extract environment-specific fields based on template
        ds_template_id = ds_data.get("type")
        if ds_template_id and ds_template_id in datasource_templates_map:
            ds_template = datasource_templates_map[ds_template_id]
            ds_data, ds_env_specific_vars = _extract_env_specific_fields(
                ds_data, ds_template, "datasource", ds_short_name, existing_env_vars or {}
            )
            # Note: This function doesn't return new_env_vars, so we can't merge them here
            # The environment variables will be handled by the calling function
        
        ds_names.append(ds_short_name)
        ds_datas.append(ds_data)
        if(write_to_file):
            ds_dir = datasources_dir / f"{ds_short_name}"
            ds_dir.mkdir(parents=True, exist_ok=True)
            _write_yaml(ds_dir / "datasource.yaml", _resolve_protected_references(ds_data, existing_env_vars=existing_env_vars, environment=environment))
            # Note: Removed config.yaml - publicId will be resolved dynamically
            console.print(f"[green]✓[/green] Saved datasource: {ds_dir / 'datasource.yaml'}")

    return ds_names, ds_datas
