"""
Task models for the NetInt API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    """Task status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class Task(BaseModel):
    """
    Represents a task in the system.

    Attributes:
        id: Task ID
        user_id: Owner user ID
        title: Task title
        description: Task description
        environment_id: Associated environment ID
        repository_id: Repository ID
        repository_name: Repository name
        repository_path: Full repository path
        branch: Git branch name
        status: Task status
        ai_status: AI execution status
        ai_prompt: AI prompt for the task
        ai_progress: AI execution progress (0-100)
        ai_error: AI execution error message
        instance_id: Associated instance ID
        instance_name: Instance name
        instance_url: Instance URL
        ask_mode: Whether task is in ask mode
        speed: Execution speed setting
        tags: Task tags
        task_metadata: Additional metadata
        mcp_servers: MCP server configurations
        git_changes: Number of git changes
        git_additions: Number of lines added
        git_deletions: Number of lines deleted
        created_at: Creation timestamp
        updated_at: Last update timestamp
        started_at: Task start timestamp
        completed_at: Task completion timestamp
        archived_at: Archive timestamp
    """

    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    environment_id: Optional[int] = None
    repository_id: Optional[str] = None
    repository_name: Optional[str] = None
    repository_path: Optional[str] = None
    branch: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    ai_status: Optional[str] = None
    ai_prompt: Optional[str] = None
    ai_progress: int = 0
    ai_error: Optional[str] = None
    instance_id: Optional[str] = None
    instance_name: Optional[str] = None
    instance_url: Optional[str] = None
    ask_mode: bool = False
    speed: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    task_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    mcp_servers: Optional[Dict[str, Any]] = Field(default_factory=dict)
    git_changes: int = 0
    git_additions: int = 0
    git_deletions: int = 0
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    @field_validator('mcp_servers', 'task_metadata', mode='before')
    @classmethod
    def ensure_dict(cls, v):
        """Convert None to empty dict for dict fields."""
        return v if v is not None else {}

    @field_validator('tags', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Convert None to empty list for list fields."""
        return v if v is not None else []

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    """
    Request model for creating a new task.

    Attributes:
        title: Task title (required)
        description: Task description
        environment_id: Associated environment ID
        ask_mode: Whether to enable ask mode
        speed: Execution speed (normal, fast, slow)
        tags: Task tags
        mcp_servers: MCP server configurations
    """

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    environment_id: Optional[int] = None
    ask_mode: bool = False
    mcp_servers: Dict[str, Any] = Field(default_factory=dict)


class TaskUpdate(BaseModel):
    """
    Request model for updating a task.

    All fields are optional - only provided fields will be updated.
    """

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    tags: Optional[List[str]] = None
    task_metadata: Optional[Dict[str, Any]] = None


class AIMessage(BaseModel):
    """
    Represents an AI message in task conversation.

    Attributes:
        id: Message ID
        task_id: Associated task ID
        role: Message role (user, assistant)
        content: Message content
        message_metadata: Additional metadata
        timestamp: Message timestamp
    """

    id: int
    task_id: int
    role: str
    content: str
    message_metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """
    Represents a chat message in task conversation.

    Attributes:
        id: Message ID
        task_id: Associated task ID
        role: Message role (user, assistant, system)
        content: Message content
        message_type: Message type (text, tool_use, etc.)
        metadata_json: Message metadata
        tokens_used: Number of tokens used
        model_used: AI model used
        session_id: Session identifier
        parent_message_id: Parent message ID
        streaming_completed: Whether streaming is completed
        timestamp: Message timestamp
    """

    id: int
    task_id: int
    role: str
    content: str
    message_type: str = "text"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = 0
    model_used: Optional[str] = None
    session_id: Optional[str] = None
    parent_message_id: Optional[int] = None
    streaming_completed: bool = True
    timestamp: datetime

    class Config:
        from_attributes = True


class SetupStatus(BaseModel):
    """
    Environment setup status.

    Attributes:
        setup_status: Status code (-1: in progress, 0: success, 1: failed)
        can_run_ai: Whether AI can be executed
        message: Status message
    """

    setup_status: Optional[int] = None
    can_run_ai: bool = False
    message: str = ""


class TaskStats(BaseModel):
    """
    Aggregated task statistics.

    Attributes:
        total_tasks: Total number of tasks
        pending_tasks: Number of pending tasks
        in_progress_tasks: Number of in-progress tasks
        completed_tasks: Number of completed tasks
        archived_tasks: Number of archived tasks
        total_git_changes: Total git changes across all tasks
        total_git_additions: Total lines added
        total_git_deletions: Total lines deleted
    """

    total_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    archived_tasks: int = 0
    total_git_changes: int = 0
    total_git_additions: int = 0
    total_git_deletions: int = 0
