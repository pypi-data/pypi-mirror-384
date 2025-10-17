"""
Environments resource for managing development environments.
"""

from typing import List, Optional

from ..models.environment import Environment, EnvironmentCreate, EnvironmentUpdate
from .base import BaseResource


class EnvironmentsResource(BaseResource):
    """
    Resource for managing development environments.

    Provides methods for CRUD operations on environments.
    """

    def list(self, repository_id: Optional[str] = None) -> List[Environment]:
        """
        List all environments for the authenticated user.

        Args:
            repository_id: Filter by repository ID (optional)

        Returns:
            List of Environment objects

        Example:
            >>> environments = client.environments.list()
            >>> for env in environments:
            ...     print(f"{env.name}: {env.repository_path}")
        """
        params = {}
        if repository_id:
            params["repository_id"] = repository_id

        data = self.http.get("/api/environments", params=params)
        return [Environment(**item) for item in data]

    def get(self, environment_id: int) -> Environment:
        """
        Get a specific environment by ID.

        Args:
            environment_id: Environment ID

        Returns:
            Environment object

        Raises:
            ResourceNotFoundError: If environment not found

        Example:
            >>> env = client.environments.get(65)
            >>> print(env.name)
        """
        data = self.http.get(f"/api/environments/{environment_id}")
        return Environment(**data)

    def create(self, environment: EnvironmentCreate) -> Environment:
        """
        Create a new environment.

        Args:
            environment: Environment creation data

        Returns:
            Created Environment object

        Example:
            >>> from netint_agents_sdk.models import EnvironmentCreate
            >>> env_data = EnvironmentCreate(
            ...     name="My Environment",
            ...     description="Development environment",
            ...     repository_path="group/project",
            ...     branch="main"
            ... )
            >>> env = client.environments.create(env_data)
        """
        data = self.http.post("/api/environments", data=environment.model_dump(exclude_none=True))
        return Environment(**data)

    def update(self, environment_id: int, updates: EnvironmentUpdate) -> Environment:
        """
        Update an existing environment.

        Args:
            environment_id: Environment ID
            updates: Fields to update

        Returns:
            Updated Environment object

        Example:
            >>> from netint_agents_sdk.models import EnvironmentUpdate
            >>> updates = EnvironmentUpdate(
            ...     description="Updated description",
            ...     branch="develop"
            ... )
            >>> env = client.environments.update(65, updates)
        """
        data = self.http.put(
            f"/api/environments/{environment_id}",
            data=updates.model_dump(exclude_none=True)
        )
        return Environment(**data)

    def delete(self, environment_id: int) -> None:
        """
        Delete an environment.

        Args:
            environment_id: Environment ID

        Example:
            >>> client.environments.delete(65)
        """
        self.http.delete(f"/api/environments/{environment_id}")
