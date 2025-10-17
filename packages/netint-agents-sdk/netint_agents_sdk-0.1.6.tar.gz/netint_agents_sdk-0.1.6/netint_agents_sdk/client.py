"""
Main NetInt API client.
"""

from typing import Optional

from .config import NetIntConfig
from .resources import (
    EnvironmentsResource,
    GitResource,
    InstancesResource,
    TasksResource,
)
from .utils.http import HTTPClient


class NetIntClient:
    """
    Main client for the NetInt Agents API.

    Provides access to all API resources through a clean, Pythonic interface.

    Attributes:
        environments: Environment management resource
        tasks: Task management resource
        instances: Instance management resource
        git: Git operations resource

    Example:
        >>> from netint_agents_sdk import NetIntClient, NetIntConfig
        >>>
        >>> # Create client with config
        >>> config = NetIntConfig(
        ...     base_url="http://localhost:8888",
        ...     api_token="svc_your_token_here"
        ... )
        >>> client = NetIntClient(config)
        >>>
        >>> # Or use environment variables
        >>> client = NetIntClient.from_env()
        >>>
        >>> # List environments
        >>> environments = client.environments.list()
        >>>
        >>> # Create a task
        >>> from netint_agents_sdk.models import TaskCreate
        >>> task = client.tasks.create(TaskCreate(
        ...     title="My Task",
        ...     description="Task description",
        ...     environment_id=65
        ... ))
        >>>
        >>> # Use context manager
        >>> with NetIntClient(config) as client:
        ...     tasks = client.tasks.list()
    """

    def __init__(self, config: Optional[NetIntConfig] = None):
        """
        Initialize NetInt API client.

        Args:
            config: NetInt configuration (uses defaults if not provided)

        Example:
            >>> config = NetIntConfig(
            ...     base_url="http://localhost:8888",
            ...     api_token="your_token"
            ... )
            >>> client = NetIntClient(config)
        """
        self.config = config or NetIntConfig()
        self._http = HTTPClient(self.config)

        # Initialize resources with reference to client for inter-resource operations
        self.environments = EnvironmentsResource(self._http, self)
        self.tasks = TasksResource(self._http, self)
        self.instances = InstancesResource(self._http, self)
        self.git = GitResource(self._http, self)

    @classmethod
    def from_env(cls) -> "NetIntClient":
        """
        Create client from environment variables.

        Environment variables:
            NETINT_BASE_URL: Base URL for the API
            NETINT_API_TOKEN: Authentication token
            NETINT_TIMEOUT: Request timeout in seconds
            NETINT_MAX_RETRIES: Maximum number of retries
            NETINT_VERIFY_SSL: Whether to verify SSL certificates

        Returns:
            NetIntClient instance configured from environment

        Example:
            >>> import os
            >>> os.environ['NETINT_API_TOKEN'] = 'your_token'
            >>> client = NetIntClient.from_env()
        """
        config = NetIntConfig.from_env()
        return cls(config)

    @classmethod
    def from_token(cls, token: str, base_url: Optional[str] = None) -> "NetIntClient":
        """
        Create client with specific token.

        Args:
            token: Authentication token (user JWT or service token)
            base_url: Base URL for the API (optional)

        Returns:
            NetIntClient instance

        Example:
            >>> client = NetIntClient.from_token("svc_your_token_here")
        """
        config = NetIntConfig(
            api_token=token,
            base_url=base_url or NetIntConfig.base_url
        )
        return cls(config)

    def close(self) -> None:
        """
        Close the HTTP client and clean up resources.

        Example:
            >>> client = NetIntClient(config)
            >>> client.close()
        """
        self._http.close()

    def __enter__(self) -> "NetIntClient":
        """
        Context manager entry.

        Example:
            >>> with NetIntClient(config) as client:
            ...     environments = client.environments.list()
        """
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return f"NetIntClient(base_url='{self.config.base_url}')"
