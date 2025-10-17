"""
Tests for the NetInt client.
"""

import pytest

from netint_agents_sdk import NetIntClient, NetIntConfig
from netint_agents_sdk.resources import (
    EnvironmentsResource,
    GitResource,
    InstancesResource,
    TasksResource,
)


def test_client_initialization():
    """Test client initialization with config."""
    config = NetIntConfig(
        base_url="http://test.example.com",
        api_token="test_token",
    )
    client = NetIntClient(config)

    assert client.config == config
    assert isinstance(client.environments, EnvironmentsResource)
    assert isinstance(client.tasks, TasksResource)
    assert isinstance(client.instances, InstancesResource)
    assert isinstance(client.git, GitResource)

    client.close()


def test_client_from_env(monkeypatch):
    """Test client creation from environment variables."""
    monkeypatch.setenv("NETINT_BASE_URL", "http://env.example.com")
    monkeypatch.setenv("NETINT_API_TOKEN", "env_token")

    client = NetIntClient.from_env()

    assert client.config.base_url == "http://env.example.com"
    assert client.config.api_token == "env_token"

    client.close()


def test_client_from_token():
    """Test client creation with token."""
    client = NetIntClient.from_token("test_token", "http://test.example.com")

    assert client.config.api_token == "test_token"
    assert client.config.base_url == "http://test.example.com"

    client.close()


def test_client_context_manager():
    """Test client as context manager."""
    config = NetIntConfig(api_token="test_token")

    with NetIntClient(config) as client:
        assert isinstance(client, NetIntClient)
        assert client.config.api_token == "test_token"


def test_client_repr():
    """Test client string representation."""
    config = NetIntConfig(base_url="http://test.example.com")
    client = NetIntClient(config)

    repr_str = repr(client)
    assert "NetIntClient" in repr_str
    assert "http://test.example.com" in repr_str

    client.close()


def test_config_defaults():
    """Test default configuration values."""
    config = NetIntConfig()

    assert config.base_url == "http://localhost:8888"
    assert config.api_token is None
    assert config.timeout == 30
    assert config.max_retries == 3
    assert config.verify_ssl is True


def test_config_with_token():
    """Test config with_token method."""
    config1 = NetIntConfig(api_token="token1", timeout=60)
    config2 = config1.with_token("token2")

    assert config1.api_token == "token1"
    assert config2.api_token == "token2"
    assert config2.timeout == 60  # Other settings preserved
