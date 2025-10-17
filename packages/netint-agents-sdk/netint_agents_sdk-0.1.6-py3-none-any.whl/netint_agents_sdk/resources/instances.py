"""
Instances resource for managing NetInt instances.
"""

from typing import Any, Dict, List, Optional

from ..models.instance import Instance, InstanceCreate, InstanceStatus
from .base import BaseResource


class InstancesResource(BaseResource):
    """
    Resource for managing NetInt instances.

    Provides methods for instance lifecycle management.
    """

    def list(self) -> List[Instance]:
        """
        List all instances for the authenticated user.

        Returns:
            List of Instance objects

        Example:
            >>> instances = client.instances.list()
            >>> for instance in instances:
            ...     print(f"{instance.instance_name}: {instance.status}")
        """
        data = self.http.get("/api/instances")
        return [Instance(**item) for item in data]

    def get(self, instance_id: str) -> Instance:
        """
        Get a specific instance by ID.

        Args:
            instance_id: Instance UUID

        Returns:
            Instance object

        Raises:
            ResourceNotFoundError: If instance not found

        Example:
            >>> instance = client.instances.get("uuid-here")
            >>> print(f"URL: {instance.instance_url}")
        """
        data = self.http.get(f"/api/instances/{instance_id}")
        return Instance(**data)

    def create(self, instance: InstanceCreate) -> Instance:
        """
        Create a new instance.

        Args:
            instance: Instance creation data

        Returns:
            Created Instance object

        Example:
            >>> from netint_agents_sdk.models import InstanceCreate
            >>> instance_data = InstanceCreate(
            ...     env_id=65,
            ...     prompt="Create hello_world.md",
            ...     is_ask_mode=False,
            ...     instance_name="my-instance",
            ...     task_id=154
            ... )
            >>> instance = client.instances.create(instance_data)
        """
        data = self.http.post("/api/instances", data=instance.model_dump(exclude_none=True))

        # The API returns a wrapper structure: {success: True, instance: {...}, ...}
        # Extract the actual instance data
        if "instance" in data:
            instance_data = data["instance"]

            # Build the Instance object from the API response structure
            # The API returns nested config/ports/paths, we need to extract what we need
            config = instance_data.get("config", {})
            ports_data = instance_data.get("ports", {})

            # Build instance_url from server_host and external_port
            server_host = config.get("server_host", "localhost")
            external_port = ports_data.get("external_port")

            instance_url = f"{self.http.config.base_url}/instance/{external_port}" if external_port else None

            # Create simplified Instance response
            simplified_data = {
                "instance_id": config.get("instance_id") or ports_data.get("instance_id"),
                "instance_name": config.get("instance_name"),
                "instance_url": instance_url,
                "status": instance_data.get("status", "unknown"),
                "ports": {
                    "external_port": ports_data.get("external_port"),
                    "ttyd_port": ports_data.get("internal_ports", {}).get("ttyd", 7681),
                    "control_plane_port": ports_data.get("internal_ports", {}).get("control_plane", 9900),
                },
                "git_info": {
                    "repo": config.get("git_repo", ""),
                    "branch": config.get("git_branch", ""),
                    "group": config.get("git_group", ""),
                },
                "created_at": instance_data.get("created_at") or ports_data.get("allocated_at"),
                "instance_auth_token": config.get("instance_auth_token"),
            }
            return Instance(**simplified_data)

        # Fallback: try to parse data directly (for backwards compatibility)
        return Instance(**data)

    def delete(self, instance_id: str) -> None:
        """
        Delete an instance.

        Args:
            instance_id: Instance UUID

        Example:
            >>> client.instances.delete("uuid-here")
        """
        self.http.delete(f"/api/instances/{instance_id}")

    def start(self, instance_id: str) -> Dict[str, Any]:
        """
        Start a stopped instance.

        Args:
            instance_id: Instance UUID

        Returns:
            Status information

        Example:
            >>> result = client.instances.start("uuid-here")
            >>> print(result['status'])
        """
        return self.http.post(f"/api/instances/{instance_id}/start")

    def stop(self, instance_id: str) -> Dict[str, Any]:
        """
        Stop a running instance.

        Args:
            instance_id: Instance UUID

        Returns:
            Status information

        Example:
            >>> result = client.instances.stop("uuid-here")
        """
        return self.http.post(f"/api/instances/{instance_id}/stop")

    def restart(self, instance_id: str) -> Dict[str, Any]:
        """
        Restart an instance.

        Args:
            instance_id: Instance UUID

        Returns:
            Status information

        Example:
            >>> result = client.instances.restart("uuid-here")
        """
        return self.http.post(f"/api/instances/{instance_id}/restart")

    def clean_restart(self, instance_id: str) -> Dict[str, Any]:
        """
        Perform a clean restart (removes persistent data).

        Args:
            instance_id: Instance UUID

        Returns:
            Status information

        Example:
            >>> result = client.instances.clean_restart("uuid-here")
        """
        return self.http.post(f"/api/instances/{instance_id}/clean-restart")

    def get_status(self, instance_id: str) -> InstanceStatus:
        """
        Get instance status and health.

        Args:
            instance_id: Instance UUID

        Returns:
            InstanceStatus object

        Example:
            >>> status = client.instances.get_status("uuid-here")
            >>> print(f"Health: {status.health}")
        """
        data = self.http.get(f"/api/instances/{instance_id}/status")
        return InstanceStatus(**data)