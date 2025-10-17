"""
Base resource class for API resources.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..utils.http import HTTPClient
    from ..client import NetIntClient


class BaseResource:
    """
    Base class for API resources.

    Provides common functionality for all resource classes.
    """

    def __init__(self, http_client: "HTTPClient", client: Optional["NetIntClient"] = None):
        """
        Initialize resource.

        Args:
            http_client: HTTP client instance
            client: Parent NetIntClient instance (optional, for inter-resource operations)
        """
        self.http = http_client
        self._client = client
