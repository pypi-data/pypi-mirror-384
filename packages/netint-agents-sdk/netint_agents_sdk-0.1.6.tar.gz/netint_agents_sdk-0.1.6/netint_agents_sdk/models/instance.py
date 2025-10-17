"""
Instance models for the NetInt API.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PortInfo(BaseModel):
    """
    Instance port information.

    Attributes:
        external_port: External nginx port
        ttyd_port: ttyd WebSocket port
        control_plane_port: Control plane API port
    """

    external_port: int
    ttyd_port: int = 7681
    control_plane_port: int = 9900


class GitInfo(BaseModel):
    """
    Git repository information.

    Attributes:
        repo: Repository name
        branch: Branch name
        group: GitLab group name
    """

    repo: str
    branch: str
    group: str


class Instance(BaseModel):
    """
    Represents a NetInt instance.

    Attributes:
        instance_id: Instance UUID
        instance_name: Instance name
        instance_url: Instance URL
        status: Instance status
        ports: Port information
        git_info: Git repository information
        created_at: Creation timestamp
        instance_auth_token: Instance service authentication token (optional)
    """

    instance_id: str
    instance_name: str
    instance_url: str
    status: str
    ports: PortInfo
    git_info: GitInfo
    created_at: datetime
    instance_auth_token: Optional[str] = None

    class Config:
        from_attributes = True


class InstanceCreate(BaseModel):
    """
    Request model for creating a new instance.

    Attributes:
        env_id: Environment ID
        prompt: Initial prompt for AI execution
        is_ask_mode: Whether to enable ask mode
        instance_name: Instance name
        task_id: Associated task ID
        mcp_servers: MCP server configurations
    """

    env_id: int
    prompt: str
    is_ask_mode: bool = False
    instance_name: Optional[str] = None
    task_id: Optional[int] = None
    mcp_servers: Optional[Dict[str, Any]] = None


class InstanceStatus(BaseModel):
    """
    Instance status information.

    Attributes:
        instance_id: Instance UUID
        status: Current status
        health: Health check status
        uptime: Uptime in seconds
        last_activity: Last activity timestamp
    """

    instance_id: str
    status: str
    health: Optional[str] = None
    uptime: Optional[int] = None
    last_activity: Optional[datetime] = None
