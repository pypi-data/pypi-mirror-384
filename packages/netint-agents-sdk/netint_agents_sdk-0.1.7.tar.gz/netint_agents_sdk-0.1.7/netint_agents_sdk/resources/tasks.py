"""
Tasks resource for managing tasks and AI execution.
"""

from typing import Dict, List, Optional

from ..models.task import (
    AIMessage,
    ChatMessage,
    SetupStatus,
    Task,
    TaskCreate,
    TaskStats,
    TaskStatus,
    TaskUpdate,
)
from .base import BaseResource


class TasksResource(BaseResource):
    """
    Resource for managing tasks and AI execution.

    Provides methods for task CRUD operations, execution monitoring,
    and message retrieval.
    """

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[TaskStatus] = None,
        repository_id: Optional[str] = None,
        search: Optional[str] = None,
        archived: bool = False,
    ) -> Dict[str, any]:
        """
        List tasks with filtering and pagination.

        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 20, max: 100)
            status: Filter by status
            repository_id: Filter by repository ID
            search: Search in title and description
            archived: Include archived tasks

        Returns:
            Dictionary with tasks, total, page, and per_page

        Example:
            >>> result = client.tasks.list(status=TaskStatus.IN_PROGRESS)
            >>> for task in result['tasks']:
            ...     print(task.title)
        """
        params = {
            "page": page,
            "per_page": min(per_page, 100),
            "archived": archived,
        }
        if status:
            params["status"] = status.value
        if repository_id:
            params["repository_id"] = repository_id
        if search:
            params["search"] = search

        data = self.http.get("/api/tasks", params=params)
        data["tasks"] = [Task(**task) for task in data["tasks"]]
        return data

    def get(self, task_id: int) -> Task:
        """
        Get a specific task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task object

        Raises:
            ResourceNotFoundError: If task not found

        Example:
            >>> task = client.tasks.get(154)
            >>> print(f"Status: {task.status}, Progress: {task.ai_progress}%")
        """
        data = self.http.get(f"/api/tasks/{task_id}")
        return Task(**data)

    def create(self, task: TaskCreate) -> Task:
        """
        Create a new task.

        Args:
            task: Task creation data

        Returns:
            Created Task object

        Example:
            >>> from netint_agents_sdk.models import TaskCreate
            >>> task_data = TaskCreate(
            ...     title="Create hello_world.md",
            ...     description="Create a hello world file",
            ...     environment_id=65,
            ...     ask_mode=False
            ... )
            >>> task = client.tasks.create(task_data)
        """
        data = self.http.post("/api/tasks", data=task.model_dump(exclude_none=True))
        return Task(**data)

    def update(self, task_id: int, updates: TaskUpdate) -> Task:
        """
        Update an existing task.

        Args:
            task_id: Task ID
            updates: Fields to update

        Returns:
            Updated Task object

        Example:
            >>> from netint_agents_sdk.models import TaskUpdate, TaskStatus
            >>> updates = TaskUpdate(
            ...     status=TaskStatus.COMPLETED,
            ...     tags=["completed", "tested"]
            ... )
            >>> task = client.tasks.update(154, updates)
        """
        data = self.http.put(
            f"/api/tasks/{task_id}",
            data=updates.model_dump(exclude_none=True)
        )
        return Task(**data)

    def delete(self, task_id: int) -> None:
        """
        Delete a task.

        Args:
            task_id: Task ID

        Example:
            >>> client.tasks.delete(154)
        """
        self.http.delete(f"/api/tasks/{task_id}")

    def link_instance(
        self,
        task_id: int,
        instance_id: str,
        instance_name: str,
        instance_url: str,
        instance_auth_token: Optional[str] = None,
    ) -> Task:
        """
        Link an instance to a task and start AI execution.

        Args:
            task_id: Task ID
            instance_id: Instance UUID
            instance_name: Instance name
            instance_url: Instance URL
            instance_auth_token: Instance service auth token (optional)

        Returns:
            Updated Task object with instance info

        Example:
            >>> task = client.tasks.link_instance(
            ...     task_id=154,
            ...     instance_id="uuid-here",
            ...     instance_name="my-instance",
            ...     instance_url="http://localhost:8102",
            ...     instance_auth_token="ist_token_here"
            ... )
        """
        request_data = {
            "instance_id": instance_id,
            "instance_name": instance_name,
            "instance_url": instance_url,
        }
        if instance_auth_token:
            request_data["instance_auth_token"] = instance_auth_token

        data = self.http.post(
            f"/api/tasks/{task_id}/link-instance",
            data=request_data
        )
        return Task(**data)

    def get_setup_status(self, task_id: int) -> SetupStatus:
        """
        Check environment setup status for a task.

        Args:
            task_id: Task ID

        Returns:
            SetupStatus object

        Example:
            >>> status = client.tasks.get_setup_status(154)
            >>> if status.can_run_ai:
            ...     print("Ready to run AI")
        """
        data = self.http.get(f"/api/tasks/{task_id}/setup-status")
        return SetupStatus(**data)

    def get_ai_messages(self, task_id: int) -> List[AIMessage]:
        """
        Get AI conversation history for a task.

        Args:
            task_id: Task ID

        Returns:
            List of AIMessage objects

        Example:
            >>> messages = client.tasks.get_ai_messages(154)
            >>> for msg in messages:
            ...     print(f"{msg.role}: {msg.content}")
        """
        data = self.http.get(f"/api/tasks/{task_id}/ai-messages")
        return [AIMessage(**msg) for msg in data]

    def get_chat_messages(
        self,
        task_id: int,
        limit: int = 50,
        offset: int = 0,
        session_id: Optional[str] = None,
    ) -> List[ChatMessage]:
        """
        Get chat message history for a task.

        Args:
            task_id: Task ID
            limit: Maximum messages to return (default: 50, max: 200)
            offset: Number of messages to skip
            session_id: Filter by session ID

        Returns:
            List of ChatMessage objects

        Example:
            >>> messages = client.tasks.get_chat_messages(154, limit=100)
            >>> for msg in messages:
            ...     print(f"{msg.role} ({msg.tokens_used} tokens): {msg.content}")
        """
        params = {
            "limit": min(limit, 200),
            "offset": offset,
        }
        if session_id:
            params["session_id"] = session_id

        data = self.http.get(f"/api/tasks/{task_id}/chat-messages", params=params)
        return [ChatMessage(**msg) for msg in data]

    def archive(self, task_id: int, archive: bool = True) -> Task:
        """
        Archive or unarchive a task.

        Args:
            task_id: Task ID
            archive: Whether to archive (True) or unarchive (False)

        Returns:
            Updated Task object

        Example:
            >>> task = client.tasks.archive(154, archive=True)
        """
        data = self.http.post(
            f"/api/tasks/{task_id}/archive",
            data={"archive": archive}
        )
        return Task(**data)

    def get_stats(self) -> TaskStats:
        """
        Get aggregated task statistics.

        Returns:
            TaskStats object with counts and totals

        Example:
            >>> stats = client.tasks.get_stats()
            >>> print(f"Total: {stats.total_tasks}, Completed: {stats.completed_tasks}")
        """
        data = self.http.get("/api/tasks/stats")
        return TaskStats(**data)

    def get_git_changes(
        self,
        task_id: int,
        include_patch: bool = True,
    ) -> Dict[str, any]:
        """
        Get git changes from the task's instance.

        This method fetches git diff information from the control plane of the
        instance associated with this task. It shows all changes made during task execution.

        Args:
            task_id: Task ID
            include_patch: Whether to include full patch/diff content (default: True)

        Returns:
            Dictionary containing git changes with the following structure:
            {
                "files_changed": int,
                "insertions": int,
                "deletions": int,
                "files": [
                    {
                        "path": str,
                        "status": str,  # "modified", "added", "deleted"
                        "insertions": int,
                        "deletions": int,
                        "patch": str,  # Full diff (if include_patch=True)
                    }
                ]
            }

        Raises:
            ValueError: If task has no instance URL
            Exception: If git changes cannot be fetched

        Example:
            >>> task = client.tasks.get(154)
            >>> changes = client.tasks.get_git_changes(task.id)
            >>> print(f"Files changed: {changes['files_changed']}")
            >>> print(f"Lines: +{changes['insertions']} -{changes['deletions']}")
            >>>
            >>> for file in changes['files']:
            ...     print(f"{file['path']}: +{file['insertions']}/-{file['deletions']}")
            ...     if include_patch:
            ...         print(file['patch'])

            >>> # Without patch content (faster)
            >>> changes = client.tasks.get_git_changes(task.id, include_patch=False)
        """
        import requests

        # Get the task to retrieve instance URL
        task = self.get(task_id)

        if not task.instance_url:
            raise ValueError(f"Task {task_id} has no associated instance URL")

        # Build the control plane API URL
        url = f"{task.instance_url}/api/git/changes"
        params = {
            "patch": "true" if include_patch else "false",
            "task_id": task_id,
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch git changes for task {task_id}: {str(e)}")

    def wait_for_completion(
        self,
        task_id: int,
        poll_interval: int = 10,
        timeout: Optional[int] = None,
        callback: Optional[callable] = None,
    ) -> Task:
        """
        Wait for a task to complete, polling for status updates.

        This method blocks until the task reaches a terminal state (succeeded or failed).
        It's useful for synchronous workflows where you want to wait for task completion.

        Args:
            task_id: Task ID to monitor
            poll_interval: Seconds between status checks (default: 10)
            timeout: Maximum seconds to wait before raising TimeoutError (default: None - no timeout)
            callback: Optional callback function called on each status update.
                     Receives the Task object as argument. Can be used for logging or custom notifications.

        Returns:
            Final Task object when completed

        Raises:
            TimeoutError: If timeout is exceeded
            Exception: If task fails with an error

        Example:
            >>> # Simple blocking wait
            >>> task = client.tasks.create_with_instance(...)
            >>> final_task = client.tasks.wait_for_completion(task.id)
            >>> print(f"Task completed with progress: {final_task.ai_progress}%")

            >>> # With custom callback for progress monitoring
            >>> def on_progress(task):
            ...     print(f"Progress: {task.ai_progress}% - {task.ai_status}")
            >>>
            >>> final_task = client.tasks.wait_for_completion(
            ...     task.id,
            ...     poll_interval=5,
            ...     timeout=600,  # 10 minutes
            ...     callback=on_progress
            ... )

            >>> # With timeout
            >>> try:
            ...     final_task = client.tasks.wait_for_completion(task.id, timeout=300)
            ... except TimeoutError:
            ...     print("Task did not complete within 5 minutes")
        """
        import time

        start_time = time.time()

        while True:
            task = self.get(task_id)

            # Call the callback if provided
            if callback:
                callback(task)

            # Check for terminal states
            if task.ai_status == "succeeded":
                return task
            elif task.ai_status == "failed":
                error_msg = task.ai_error or "Task failed without error message"
                raise Exception(f"Task {task_id} failed: {error_msg}")

            # Check timeout
            if timeout:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise TimeoutError(
                        f"Task {task_id} did not complete within {timeout} seconds. "
                        f"Current status: {task.ai_status}, Progress: {task.ai_progress}%"
                    )

            # Wait before next poll
            time.sleep(poll_interval)

    def create_with_instance(
        self,
        title: str,
        prompt: str,
        environment_id: int,
        description: Optional[str] = None,
        ask_mode: bool = False,
        instance_name: Optional[str] = None,
        mcp_servers: Optional[Dict[str, any]] = None,
    ) -> Task:
        """
        Convenience method: Create a task and automatically provision an instance for it.

        This is a high-level method that combines three operations:
        1. Create the task
        2. Create a linked instance
        3. Link the instance to the task

        Args:
            title: Task title
            prompt: Initial prompt/command for the AI agent
            environment_id: Environment ID to run in
            description: Task description (optional)
            ask_mode: Enable ask mode for interactive approval (default: False)
            instance_name: Custom instance name (optional, auto-generated if not provided)
            mcp_servers: MCP server configurations (optional)

        Returns:
            Task object with instance already linked and AI execution started

        Example:
            >>> # Simple one-liner task creation
            >>> task = client.tasks.create_with_instance(
            ...     title="Create hello_world.md",
            ...     prompt="Create a hello world markdown file",
            ...     environment_id=65,
            ...     description="Simple hello world task"
            ... )
            >>> print(f"Task {task.id} running at {task.instance_url}")

        Note:
            This method may take a few minutes to complete as it waits for
            instance provisioning. Use the lower-level create() method if you
            need more control over the workflow.
        """
        from ..models.instance import InstanceCreate

        # Step 1: Create the task
        task_data = TaskCreate(
            title=title,
            description=description,
            environment_id=environment_id,
            ask_mode=ask_mode,
            mcp_servers=mcp_servers or {},
        )
        task = self.create(task_data)

        # Step 2: Create instance with task_id
        instance_data = InstanceCreate(
            env_id=environment_id,
            prompt=prompt,
            is_ask_mode=ask_mode,
            instance_name=instance_name or f"task-{task.id}",
            task_id=task.id,
            mcp_servers=mcp_servers or {},
        )

        # Use the parent client's instances resource
        if not self._client:
            raise RuntimeError("Client reference not available. This method requires the full client context.")

        instance = self._client.instances.create(instance_data)

        # Step 3: Link instance to task
        task = self.link_instance(
            task_id=task.id,
            instance_id=instance.instance_id,
            instance_name=instance.instance_name,
            instance_url=instance.instance_url,
            instance_auth_token=instance.instance_auth_token,
        )

        return task
