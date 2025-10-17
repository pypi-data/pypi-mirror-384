"""Data models for agents."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AgentType(Enum):
    """Agent type enumeration."""
    CONVERSATIONAL = "conversational"
    TASK_ORIENTED = "task_oriented"
    WORKFLOW = "workflow"


class AgentStatus(Enum):
    """Agent status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPLOYED = "deployed"


@dataclass
class AgentConfig:
    """Agent configuration model."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: Optional[str] = None
    few_shot_examples: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
            "few_shot_examples": self.few_shot_examples
        }


@dataclass
class AgentMetadata:
    """Agent metadata model."""
    tags: List[str]
    owners: List[str]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tags": self.tags,
            "owners": self.owners,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }


@dataclass
class Agent:
    """Agent model."""
    name: str
    description: str
    type: AgentType
    config: AgentConfig
    version: str = "1.0.0"
    status: AgentStatus = AgentStatus.DRAFT
    tools: List[Dict[str, Any]] = None
    datasources: List[Dict[str, Any]] = None
    metadata: Optional[AgentMetadata] = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        if self.datasources is None:
            self.datasources = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "version": self.version,
            "status": self.status.value,
            "config": self.config.to_dict(),
            "tools": self.tools,
            "datasources": self.datasources
        }
        
        if self.metadata:
            result["metadata"] = self.metadata.to_dict()
            
        return result
