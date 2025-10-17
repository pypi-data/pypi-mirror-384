"""Login command for authenticating with Canvas platform."""

from typing import Optional
import click
import requests
from rich.console import Console
from rich.prompt import Prompt

from ..utils.config import ConfigManager, Profile
from ..utils.exceptions import AuthenticationError
from ..services.api_client import APIClient
from ..utils.helpers import require_canvas_workspace

console = Console()


@click.command()
@click.option(
    "--api-base",
    help="API base URL (e.g., https://api.canvas.raga.ai)"
)
@click.option(
    "--access-key",
    help="Access key"
)
@click.option(
    "--secret-key",
    help="Secret key"
)
@click.option(
    "--profile",
    help="Profile name to save credentials under",
    required=True
)
def login(api_base: Optional[str], access_key: Optional[str], secret_key: Optional[str], profile: Optional[str]) -> None:
    """Authenticate with Canvas platform and save credentials."""
    
    # Validate we're in a Canvas workspace
    require_canvas_workspace()
    
    try:
        console.print("[blue]Canvas Platform Login[/blue]")
        console.print("Please provide your Canvas platform credentials.\n")
        
        # Get profile name
        if not profile:
            profile = Prompt.ask(
                "Profile name",
                default="default"
            )
        
        # Get API base URL
        if not api_base:
            api_base = Prompt.ask(
                "Backend URL",
                default="https://api.canvas.raga.ai"
            )
        api_base = api_base.rstrip('/')
        
        # Prompt for username (email) and password
        if not access_key:
            access_key = Prompt.ask("access_key")
        if not secret_key:
            secret_key = Prompt.ask("secret_key", password=True)
        
        # Authenticate to obtain token
        console.print("\n[yellow]Authenticating...[/yellow]")
        auth_url = f"{api_base}/api/credentials/token"
        try:
            resp = requests.post(
                auth_url,
                json={"accessKey": access_key, "secretKey": secret_key},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
        except requests.exceptions.ConnectionError:
            raise AuthenticationError(f"Could not connect to {auth_url}. Please check the URL.")
        except requests.exceptions.Timeout:
            raise AuthenticationError("Authentication request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Authentication request failed: {e}")
        
        if resp.status_code != 200:
            # Try to extract error message
            err_msg = f"Authentication failed with status {resp.status_code}"
            try:
                data = resp.json()
                msg = None
                if isinstance(data, dict):
                    msg = data.get("message") or data.get("error")
                if msg:
                    err_msg = msg
            except Exception:
                pass
            raise AuthenticationError(err_msg)
        
        # Extract token from response
        try:
            data = resp.json() or {}
        except Exception:
            raise AuthenticationError("Authentication response was not valid JSON")
        
        token = data.get("token") or ((data.get("data") or {}).get("token"))
        if not token:
            raise AuthenticationError("Authentication succeeded but no token was returned")
        
        # Validate credentials using token
        console.print("[yellow]Validating credentials...[/yellow]")
        if not _validate_credentials(api_base, token):
            raise AuthenticationError("Token invalid or unable to reach API")
        
        # Save profile
        config_manager = ConfigManager()
        user_profile = Profile(
            name=profile,
            api_base=api_base,
            token=token
        )
        
        config_manager.add_profile(user_profile)
        config_manager.set_current_profile(profile)
        
        console.print(f"[green]✓[/green] Successfully authenticated and saved profile '{profile}'")
        console.print(f"[blue]API Base:[/blue] {api_base}")
        console.print(f"[blue]Profile:[/blue] {profile}")
        
        # Test API connection
        console.print("\n[yellow]Testing API connection...[/yellow]")
        api_client = APIClient(profile=user_profile)
        
        try:
            projects = api_client.list_projects()
            project_count = len(projects) if projects else 0
            console.print(f"[green]✓[/green] Connected successfully! Found {project_count} projects.")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not fetch projects: {e}")
            console.print("[yellow]Authentication saved, but API connection may have issues.[/yellow]")
        
        console.print("\n[blue]Next steps:[/blue]")
        console.print("• Run [cyan]canvas list projects[/cyan] to see your projects")
        console.print("• Run [cyan]canvas init[/cyan] to create a new workspace")
        
    except AuthenticationError as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Login failed:[/red] {e}")
        raise click.Abort()


def _validate_credentials(api_base: str, token: str) -> bool:
    """Validate credentials against the API."""
    try:
        # Clean up API base URL
        api_base = api_base.rstrip('/')
        
        # Try to make a test request to validate credentials
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test with a simple endpoint - trying to get projects
        response = requests.get(
            f"{api_base}/api/projects",
            headers=headers,
            timeout=30
        )
        
        # Consider 200 OK or 403 Forbidden as valid (token is recognized)
        # 401 Unauthorized means invalid token
        # Connection errors or other status codes are also failures
        
        if response.status_code == 200:
            return True
        elif response.status_code == 403:
            # Token is valid but user might not have project access
            return True
        elif response.status_code == 401:
            return False
        else:
            # Other errors - could be server issues
            console.print(f"[yellow]Warning:[/yellow] API returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        raise AuthenticationError(f"Could not connect to {api_base}. Please check the URL.")
    except requests.exceptions.Timeout:
        raise AuthenticationError("Request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise AuthenticationError(f"Request failed: {e}")
    except Exception as e:
        raise AuthenticationError(f"Validation failed: {e}")
