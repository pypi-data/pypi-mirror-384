"""
Pydantic models for NetInt API entities.
"""

from .environment import Environment, EnvironmentCreate, EnvironmentUpdate
from .task import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskStatus,
    AIMessage,
    ChatMessage,
    SetupStatus,
    TaskStats,
)
from .instance import Instance, InstanceCreate, InstanceStatus, PortInfo, GitInfo
from .git import GitChanges, GitStatus, GitFile, CommitResult, PushResult

__all__ = [
    # Environment models
    "Environment",
    "EnvironmentCreate",
    "EnvironmentUpdate",
    # Task models
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "TaskStatus",
    "AIMessage",
    "ChatMessage",
    "SetupStatus",
    "TaskStats",
    # Instance models
    "Instance",
    "InstanceCreate",
    "InstanceStatus",
    "PortInfo",
    "GitInfo",
    # Git models
    "GitChanges",
    "GitStatus",
    "GitFile",
    "CommitResult",
    "PushResult",
]
