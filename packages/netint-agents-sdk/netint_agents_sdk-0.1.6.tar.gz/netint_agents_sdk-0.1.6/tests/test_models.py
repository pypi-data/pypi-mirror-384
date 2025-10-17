"""
Tests for Pydantic models.
"""

from datetime import datetime

import pytest

from netint_agents_sdk.models import (
    Environment,
    EnvironmentCreate,
    Task,
    TaskCreate,
    TaskStatus,
    Instance,
    InstanceCreate,
    GitChanges,
    GitStatus,
)


def test_environment_create():
    """Test EnvironmentCreate model."""
    env_data = EnvironmentCreate(
        name="Test Environment",
        description="Test description",
        repository_path="group/project",
        branch="main",
    )

    assert env_data.name == "Test Environment"
    assert env_data.description == "Test description"
    assert env_data.repository_path == "group/project"
    assert env_data.branch == "main"


def test_environment_create_validation():
    """Test EnvironmentCreate validation."""
    with pytest.raises(Exception):  # Pydantic validation error
        EnvironmentCreate(name="")  # Empty name should fail


def test_task_create():
    """Test TaskCreate model."""
    task_data = TaskCreate(
        title="Test Task",
        description="Test description",
        environment_id=65,
        ask_mode=False,
        tags=["test", "example"],
    )

    assert task_data.title == "Test Task"
    assert task_data.description == "Test description"
    assert task_data.environment_id == 65
    assert task_data.ask_mode is False
    assert task_data.tags == ["test", "example"]


def test_task_status_enum():
    """Test TaskStatus enum values."""
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"


def test_instance_create():
    """Test InstanceCreate model."""
    instance_data = InstanceCreate(
        env_id=65,
        prompt="Test prompt",
        is_ask_mode=False,
        instance_name="test-instance",
        task_id=154,
    )

    assert instance_data.env_id == 65
    assert instance_data.prompt == "Test prompt"
    assert instance_data.is_ask_mode is False
    assert instance_data.instance_name == "test-instance"
    assert instance_data.task_id == 154


def test_model_serialization():
    """Test model serialization to dict."""
    task_data = TaskCreate(
        title="Test",
        description="Description",
        environment_id=65,
        tags=["test"],
    )

    data_dict = task_data.model_dump()

    assert data_dict["title"] == "Test"
    assert data_dict["description"] == "Description"
    assert data_dict["environment_id"] == 65
    assert "test" in data_dict["tags"]


def test_model_deserialization():
    """Test model deserialization from dict."""
    data = {
        "id": 154,
        "user_id": 1,
        "title": "Test Task",
        "description": "Description",
        "status": "pending",
        "ai_progress": 50,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
    }

    task = Task(**data)

    assert task.id == 154
    assert task.title == "Test Task"
    assert task.status == TaskStatus.PENDING
    assert task.ai_progress == 50
