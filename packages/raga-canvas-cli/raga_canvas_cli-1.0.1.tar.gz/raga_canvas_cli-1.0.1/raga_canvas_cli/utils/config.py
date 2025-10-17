"""Configuration management for Raga Canvas CLI."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import keyring
from dataclasses import dataclass, asdict
from .exceptions import ConfigurationError


@dataclass
class Profile:
    """User profile configuration."""
    name: str
    api_base: str
    token: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CanvasConfig:
    """Canvas workspace configuration."""
    name: str
    version: str = "1.0"
    default_environment: str = "dev"
    registry_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ConfigManager:
    """Manages configuration files and profiles."""
    
    def __init__(self):
        self.home_dir = Path.home()
        self.config_file = self.home_dir / ".canvasrc"
        self.workspace_config = Path("canvas.yaml")
        
    def load_global_config(self) -> Dict[str, Any]:
        """Load global configuration from ~/.canvasrc."""
        if not self.config_file.exists():
            return {"profiles": {}, "current_profile": None}
            
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {e}")
    
    def save_global_config(self, config: Dict[str, Any]) -> None:
        """Save global configuration to ~/.canvasrc."""
        try:
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False)
        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {e}")
    
    def add_profile(self, profile: Profile) -> None:
        """Add or update a profile."""
        config = self.load_global_config()
        
        if "profiles" not in config:
            config["profiles"] = {}
            
        # Store token in keyring if available
        if profile.token:
            try:
                keyring.set_password("raga-canvas-cli", profile.name, profile.token)
                # Don't store token in file
                profile_dict = profile.to_dict()
                profile_dict.pop("token", None)
            except Exception:
                # Fallback to storing in file if keyring fails
                profile_dict = profile.to_dict()
        else:
            profile_dict = profile.to_dict()
            
        config["profiles"][profile.name] = profile_dict
        
        # Set as current if it's the first profile
        if not config.get("current_profile"):
            config["current_profile"] = profile.name
            
        self.save_global_config(config)
        
        # Also save profile config to workspace profiles/ directory (for CI/CD)
        self._save_workspace_profile(profile)
    
    def get_profile(self, name: Optional[str] = None) -> Optional[Profile]:
        """Get a profile by name or current profile."""
        config = self.load_global_config()
        
        if not name:
            name = config.get("current_profile")
            
        if not name:
            return None
            
        # First try to get profile from global config
        profile_data = config.get("profiles", {}).get(name)
        
        # If not found in global config, try workspace profiles
        if not profile_data:
            workspace_profile = self._load_workspace_profile(name)
            if workspace_profile:
                profile_data = workspace_profile
            else:
                return None
        
        # Try to get token from keyring (credentials are never in workspace profiles)
        token = None
        try:
            token = keyring.get_password("raga-canvas-cli", name)
        except Exception:
            pass
            
        # Fallback to token in global config file (not workspace profiles)
        if not token and name in config.get("profiles", {}):
            token = config["profiles"][name].get("token")
            
        return Profile(
            name=profile_data["name"],
            api_base=profile_data["api_base"],
            token=token
        )
    
    def set_current_profile(self, name: str) -> None:
        """Set the current active profile."""
        config = self.load_global_config()
        
        if name not in config.get("profiles", {}):
            raise ConfigurationError(f"Profile '{name}' not found")
            
        config["current_profile"] = name
        self.save_global_config(config)
    
    def list_profiles(self) -> Dict[str, Dict[str, Any]]:
        """List all profiles."""
        config = self.load_global_config()
        return config.get("profiles", {})
    
    def load_workspace_config(self) -> Optional[CanvasConfig]:
        """Load workspace configuration from canvas.yaml."""
        if not self.workspace_config.exists():
            return None
            
        try:
            with open(self.workspace_config, 'r') as f:
                data = yaml.safe_load(f)
                return CanvasConfig(**data)
        except Exception as e:
            raise ConfigurationError(f"Failed to load workspace config: {e}")
    
    def save_workspace_config(self, config: CanvasConfig) -> None:
        """Save workspace configuration to canvas.yaml."""
        try:
            with open(self.workspace_config, 'w') as f:
                yaml.safe_dump(config.to_dict(), f, default_flow_style=False)
        except Exception as e:
            raise ConfigurationError(f"Failed to save workspace config: {e}")
    
    def load_environment_config(self, env_name: str) -> Dict[str, Any]:
        """Load environment-specific configuration."""
        env_file = Path("env") / f"{env_name}.yaml"
        
        if not env_file.exists():
            return {}
            
        try:
            with open(env_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to load environment config: {e}")
    
    def get_effective_config(self, env_name: Optional[str] = None) -> Dict[str, Any]:
        """Get the effective configuration by merging base and environment configs."""
        workspace_config = self.load_workspace_config()
        if not workspace_config:
            raise ConfigurationError("No workspace configuration found. Run 'canvas init' first.")
        
        if not env_name:
            env_name = workspace_config.default_environment
            
        base_config = workspace_config.to_dict()
        env_config = self.load_environment_config(env_name)
        
        # Merge configurations (env overrides base)
        effective_config = {**base_config, **env_config}
        
        return effective_config

    def get_default_project(self) -> Optional[str]:
        """Get the default project from config.yaml."""
        default_project = self.load_workspace_config().name
        if not default_project:
            raise ConfigurationError("No default project found. Run 'canvas init' first.")
        return default_project
    
    def _save_workspace_profile(self, profile: Profile) -> None:
        """Save profile configuration to workspace profiles/ directory (for CI/CD)."""
        profiles_dir = Path("profiles")
        if not profiles_dir.exists():
            return  # Skip if we're not in a Canvas workspace
            
        try:
            profiles_dir.mkdir(parents=True, exist_ok=True)
            
            # Create profile config without sensitive data
            profile_config = {
                "name": profile.name,
                "api_base": profile.api_base,
                "created_at": None,  # Could add timestamp if needed
                # Note: token is NOT stored here for security
            }
            
            profile_file = profiles_dir / f"{profile.name}.yaml"
            with open(profile_file, 'w') as f:
                yaml.safe_dump(profile_config, f, default_flow_style=False)
                
        except Exception:
            # Silently fail if we can't save workspace profile
            # The global profile is still saved successfully
            pass
    
    def _load_workspace_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Load profile configuration from workspace profiles/ directory."""
        profiles_dir = Path("profiles")
        if not profiles_dir.exists():
            return None
            
        profile_file = profiles_dir / f"{name}.yaml"
        if not profile_file.exists():
            return None
            
        try:
            with open(profile_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return None