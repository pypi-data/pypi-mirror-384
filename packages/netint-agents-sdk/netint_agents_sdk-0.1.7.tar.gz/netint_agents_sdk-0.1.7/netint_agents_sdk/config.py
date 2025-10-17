"""
Configuration management for the NetInt Agents SDK.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class NetIntConfig:
    """
    Configuration for NetInt API client.

    Args:
        base_url: Base URL for the NetInt API (default: http://localhost:8888)
        api_token: Authentication token (user JWT or service token)
        timeout: Request timeout in seconds (default: 600)
        max_retries: Maximum number of retries for failed requests (default: 3)
        verify_ssl: Whether to verify SSL certificates (default: True)
        debug: Enable debug logging for requests/responses (default: False)

    Example:
        >>> config = NetIntConfig(
        ...     base_url="http://localhost:8888",
        ...     api_token="svc_your_token_here",
        ...     debug=True
        ... )
    """

    base_url: str = "http://localhost:8888"
    api_token: Optional[str] = None
    timeout: int = 600  # 10 minutes
    max_retries: int = 1
    verify_ssl: bool = True
    debug: bool = False

    @classmethod
    def from_env(cls) -> "NetIntConfig":
        """
        Create configuration from environment variables.

        Environment variables:
            NETINT_BASE_URL: Base URL for the API
            NETINT_API_TOKEN: Authentication token
            NETINT_TIMEOUT: Request timeout in seconds
            NETINT_MAX_RETRIES: Maximum number of retries
            NETINT_VERIFY_SSL: Whether to verify SSL certificates

        Returns:
            NetIntConfig instance with values from environment

        Example:
            >>> config = NetIntConfig.from_env()
        """
        return cls(
            base_url=os.getenv("NETINT_BASE_URL", cls.base_url),
            api_token=os.getenv("NETINT_API_TOKEN"),
            timeout=int(os.getenv("NETINT_TIMEOUT", str(cls.timeout))),
            max_retries=int(os.getenv("NETINT_MAX_RETRIES", str(cls.max_retries))),
            verify_ssl=os.getenv("NETINT_VERIFY_SSL", "true").lower() == "true",
            debug=os.getenv("NETINT_DEBUG", "false").lower() == "true",
        )

    def with_token(self, token: str) -> "NetIntConfig":
        """
        Create a new config with a different token.

        Args:
            token: New authentication token

        Returns:
            New NetIntConfig instance with updated token

        Example:
            >>> new_config = config.with_token("new_token")
        """
        return NetIntConfig(
            base_url=self.base_url,
            api_token=token,
            timeout=self.timeout,
            max_retries=self.max_retries,
            verify_ssl=self.verify_ssl,
            debug=self.debug,
        )
