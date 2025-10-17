"""API client for Canvas platform."""

import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

from ..utils.config import Profile
from ..utils.exceptions import APIError, AuthenticationError


class APIClient:
    """Client for interacting with Canvas platform API."""
    
    def __init__(self, profile: Profile):
        self.profile = profile
        self.base_url = profile.api_base.rstrip('/')
        self.session = requests.Session()
        
        if profile.token:
            self.session.headers.update({
                "Authorization": f"Bearer {profile.token}",
                "Content-Type": "application/json"
            })
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """Make HTTP request to the API."""
        url = urljoin(self.base_url + "/", endpoint.lstrip('/'))
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=timeout_seconds
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed. Please run 'canvas login'")
            elif response.status_code == 403:
                raise APIError("Access denied. Check your permissions.")
            elif response.status_code >= 400:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and "message" in error_data:
                        error_msg = error_data["message"]
                except:
                    pass
                raise APIError(error_msg)
            
            try:
                return response.json()
            except ValueError as e:
                raise APIError(f"Invalid JSON response from API: {e}")
            except Exception as e:
                raise APIError(f"Failed to parse API response: {e}")
            
        except requests.exceptions.ConnectionError:
            raise APIError(f"Could not connect to {self.base_url}")
        except requests.exceptions.Timeout:
            raise APIError("Request timed out")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        response = self._make_request("GET", "/api/projects")
        data = response.get("data", [])
        
        # Ensure we return a list
        if not isinstance(data, list):
            raise APIError(f"Expected list of projects, got {type(data).__name__}: {data}")
        
        return data
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details."""
        response = self._make_request("GET", f"/api/projects/{project_id}")
        return response.get("data", {})
    
    def list_agents(self, project_id: str, folder_id: Optional[str] = None, 
                   search: Optional[str] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """List agents in a project."""
        params = {}
        if folder_id:
            params["folderId"] = folder_id
        if search:
            params["search"] = search
        if is_active is not None:
            params["isActive"] = is_active
            
        response = self._make_request("GET", f"/api/projects/{project_id}/agents", params=params)
        data = response.get("data", [])
        
        # Ensure we return a list
        if not isinstance(data, list):
            raise APIError(f"Expected list of agents, got {type(data).__name__}: {data}")
        
        return data
    
    def get_agent(self, project_id: str, agent_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get agent details."""
        params = {}
        if version:
            params["version"] = version
            
        response = self._make_request("GET", f"/api/projects/{project_id}/agents/{agent_id}", params=params)
        return response.get("data", {})
    
    def get_agent_by_short_name(self, project_id: str, short_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get agent details."""
        params = {"isShortName": True}
        if version:
            params["version"] = version
            
        response = self._make_request("GET", f"/api/projects/{project_id}/agents/{short_name}", params=params)
        return response.get("data", {})

    def create_agent(self, project_id: str, agent_config: Dict[str, Any], short_name: str) -> Dict[str, Any]:
        """Create a new agent."""
        response = self._make_request("POST", f"/api/projects/{project_id}/agents", params={"shortName": short_name}, data={"agentConfig": agent_config})
        return response.get("data", {})
    
    def update_agent(self, project_id: str, agent_id: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing agent."""
        response = self._make_request("PUT", f"/api/projects/{project_id}/agents/{agent_id}", data={"agentConfig": agent_config})
        return response.get("data", {})
    
    def deploy_agent(self, project_id: str, agent_id: str, version: Optional[str] = None, 
                    hard_reload: bool = False) -> Dict[str, Any]:
        """Deploy an agent."""
        params = {}
        if version:
            params["version"] = version
        if hard_reload:
            params["hardReload"] = hard_reload
        
        try:
            response = self._make_request(
                "POST",
                f"/api/projects/{project_id}/agents/{agent_id}/deploy",
                params=params,
                timeout_seconds=180
            )
            return response.get("data", {})
        except APIError as e:
            # Retry once on timeout
            if "timed out" in str(e).lower():
                response = self._make_request(
                    "POST",
                    f"/api/projects/{project_id}/agents/{agent_id}/deploy",
                    params=params,
                    timeout_seconds=300
                )
                return response.get("data", {})
            raise
    
    def list_tools(self, project_id: str, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tools in a project."""
        params = {}
        if search:
            params["search"] = search
            
        response = self._make_request("GET", f"/api/projects/{project_id}/list-tools", params=params)
        return response.get("data", {})
    
    def get_tool(self, project_id: str, tool_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get tool details."""
        params = {}
        if version:
            params["version"] = version
            
        response = self._make_request("GET", f"/api/projects/{project_id}/tools/{tool_id}", params=params)
        return response.get("data", {})
    
    def get_tool_by_short_name(self, project_id: str, short_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get tool details."""
        params = {"isShortName": True}
        if version:
            params["version"] = version
        response = self._make_request("GET", f"/api/projects/{project_id}/tools/{short_name}", params=params)
        return response.get("data", {})
    
    def create_tool(self, project_id: str, tool_config: Dict[str, Any], short_name: str) -> Dict[str, Any]:
        """Create a new tool."""
        response = self._make_request("POST", f"/api/projects/{project_id}/tools", params={"shortName": short_name}, data={"toolConfig": tool_config})
        return response.get("data", {})
    
    def update_tool(self, project_id: str, tool_id: str, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing tool."""
        response = self._make_request("PUT", f"/api/projects/{project_id}/tools/{tool_id}", data={"toolConfig": tool_config})
        return response.get("data", {})
    
    def list_datasources(self, project_id: str, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """List datasources in a project."""
        params = {}
        if search:
            params["search"] = search
            
        response = self._make_request("GET", f"/api/projects/{project_id}/list-datasources", params=params)
        return response.get("data", {})
    
    def get_datasource_by_short_name(self, project_id: str, short_name: str) -> Dict[str, Any]:
        """Get datasource details by short name."""
        response = self._make_request("GET", f"/api/projects/{project_id}/datasources/{short_name}", params={"isShortName": True})
        return response.get("data", {})
    
    def get_datasource(self, project_id: str, datasource_id: str) -> Dict[str, Any]:
        """Get datasource details."""
        response = self._make_request("GET", f"/api/projects/{project_id}/datasources/{datasource_id}")
        return response.get("data", {})
    
    def create_datasource(self, project_id: str, datasource_config: Dict[str, Any], short_name: str) -> Dict[str, Any]:
        """Create a new datasource."""
        response = self._make_request("POST", f"/api/projects/{project_id}/datasources", params={"shortName": short_name}, data={"dataSourceConfig": datasource_config})
        return response.get("data", {})
    
    def update_datasource(self, project_id: str, datasource_id: str, datasource_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing datasource."""
        response = self._make_request("PUT", f"/api/projects/{project_id}/datasources/{datasource_id}", data={"dataSourceConfig": datasource_config})
        return response.get("data", {})
    
    def list_workflows(self, project_id: str, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List workflows in a project."""
        params = {}
        if folder_id:
            params["folderId"] = folder_id
            
        response = self._make_request("GET", f"/api/projects/{project_id}/workflows", params=params)
        return response.get("data", [])
    
    def get_workflow(self, project_id: str, workflow_id: str, version_id: Optional[str] = None) -> Dict[str, Any]:
        """Get workflow details."""
        params = {}
        if version_id:
            params["versionId"] = version_id
            
        response = self._make_request("GET", f"/api/projects/{project_id}/workflows/{workflow_id}", params=params)
        return response.get("data", {})

    # New upsert-style push endpoints
    def push_agent(self, project_id: str, agent_id: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update an agent by ID (upsert)."""
        payload = {"agentConfig": agent_config}
        response = self._make_request("PUT", f"/api/projects/{project_id}/agents/{agent_id}", data=payload)
        return response.get("data", {})

    def push_tool(self, project_id: str, tool_id: str, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a tool by ID (upsert)."""
        payload = {"toolConfig": tool_config}
        response = self._make_request("PUT", f"/api/projects/{project_id}/tools/{tool_id}", data=payload)
        return response.get("data", {})

    def push_datasource(self, project_id: str, datasource_id: str, datasource_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a datasource by ID (upsert)."""
        payload = {"dataSourceConfig": datasource_config}
        response = self._make_request("PUT", f"/api/projects/{project_id}/datasources/{datasource_id}", data=payload)
        return response.get("data", {})

    def list_tool_templates(self) -> List[Dict[str, Any]]:
        """List tool templates."""
        response = self._make_request("GET", "/api/templates/tools")
        return response.get("data", [])
    
    def list_datasource_templates(self) -> List[Dict[str, Any]]:
        """List datasource templates."""
        response = self._make_request("GET", "/api/templates/dataSources")
        return response.get("data", [])
    
    def get_project_jwt_public_key(self, project_id: str) -> Dict[str, Any]:
        """Get JWT public key for a project."""
        response = self._make_request("GET", f"/api/projects/{project_id}/jwt-public-key")
        return response.get("data", {})
    
    def update_project_jwt_public_key(self, project_id: str, public_key: str) -> Dict[str, Any]:
        """Update JWT public key for a project."""
        payload = {"publicKey": public_key}
        response = self._make_request("POST", f"/api/projects/{project_id}/jwt-public-key", data=payload)
        return response.get("data", {})