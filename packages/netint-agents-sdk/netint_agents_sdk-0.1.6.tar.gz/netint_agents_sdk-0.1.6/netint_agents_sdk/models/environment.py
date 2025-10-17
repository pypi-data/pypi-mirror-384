"""
Environment models for the NetInt API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Environment(BaseModel):
    """
    Represents a development environment.

    Attributes:
        id: Environment ID
        env_id: UUID string identifier
        name: Environment name
        description: Environment description
        repository_id: GitLab repository ID
        repository_name: Repository name
        repository_path: Full repository path (group/project)
        branch: Git branch name
        script_content: Setup script content
        script_path: Path to setup script
        commands: List of recorded commands
        mcp_servers: MCP server configurations
        user_id: Owner user ID
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: int
    env_id: str
    name: str
    description: Optional[str] = None
    repository_id: Optional[str] = None
    repository_name: Optional[str] = None
    repository_path: Optional[str] = None
    branch: str = "main"
    script_content: Optional[str] = None
    script_path: Optional[str] = None
    commands: List[str] = Field(default_factory=list)
    mcp_servers: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user_id: int
    created_at: datetime
    updated_at: datetime

    @field_validator('mcp_servers', mode='before')
    @classmethod
    def ensure_dict(cls, v):
        """Convert None to empty dict."""
        return v if v is not None else {}

    @field_validator('commands', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Convert None to empty list."""
        return v if v is not None else []

    class Config:
        from_attributes = True


class EnvironmentCreate(BaseModel):
    """
    Request model for creating a new environment.

    Attributes:
        name: Environment name (required)
        description: Environment description
        repository_id: GitLab repository ID
        repository_name: Repository name
        repository_path: Full repository path (group/project)
        branch: Git branch name (default: main)
        script_content: Setup script content
        script_path: Path to setup script
        commands: List of setup commands
        mcp_servers: MCP server configurations
    """

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    repository_id: Optional[str] = None
    repository_name: Optional[str] = None
    repository_path: Optional[str] = None
    branch: str = "main"
    script_content: Optional[str] = None
    script_path: Optional[str] = None
    commands: List[str] = Field(default_factory=list)
    mcp_servers: Dict[str, Any] = Field(default_factory=dict)


class EnvironmentUpdate(BaseModel):
    """
    Request model for updating an environment.

    All fields are optional - only provided fields will be updated.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    repository_id: Optional[str] = None
    repository_name: Optional[str] = None
    repository_path: Optional[str] = None
    branch: Optional[str] = None
    script_content: Optional[str] = None
    script_path: Optional[str] = None
    commands: Optional[List[str]] = None
    mcp_servers: Optional[Dict[str, Any]] = None
