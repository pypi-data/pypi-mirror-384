"""
Git operations resource for managing repository changes.
"""

from typing import Optional

from ..models.git import CommitResult, GitChanges, GitStatus, PushResult
from .base import BaseResource


class GitResource(BaseResource):
    """
    Resource for git operations on instances.

    Note: Git operations use instance-specific URLs from the
    instance.instance_url field.
    """

    def get_changes(
        self,
        instance_url: str,
        task_id: int,
        include_patch: bool = False,
    ) -> GitChanges:
        """
        Get git changes (diff) for a task.

        Args:
            instance_url: Instance URL (from instance.instance_url)
            task_id: Task ID
            include_patch: Include full patch/diff content

        Returns:
            GitChanges object with repository and change information

        Example:
            >>> changes = client.git.get_changes(
            ...     instance_url="http://localhost:8102",
            ...     task_id=154,
            ...     include_patch=True
            ... )
            >>> print(f"Total files changed: {changes.changes.total_files}")
            >>> for file in changes.changes.files:
            ...     print(f"  {file.path}: +{file.additions} -{file.deletions}")
        """
        params = {
            "task_id": task_id,
            "patch": include_patch,
        }
        url = f"{instance_url}/api/git/changes"
        data = self.http.get(url, params=params)
        return GitChanges(**data)

    def get_status(self, instance_url: str, task_id: int) -> GitStatus:
        """
        Get git repository status.

        Args:
            instance_url: Instance URL
            task_id: Task ID

        Returns:
            GitStatus object with staged, unstaged, and untracked files

        Example:
            >>> status = client.git.get_status(
            ...     instance_url="http://localhost:8102",
            ...     task_id=154
            ... )
            >>> print(f"Branch: {status.branch}")
            >>> print(f"Staged files: {len(status.staged)}")
            >>> print(f"Clean: {status.clean}")
        """
        params = {"task_id": task_id}
        url = f"{instance_url}/api/git/status"
        data = self.http.get(url, params=params)
        return GitStatus(**data)

    def commit_unstaged(self, instance_url: str, task_id: int) -> CommitResult:
        """
        Commit unstaged changes with auto-generated message.

        Args:
            instance_url: Instance URL
            task_id: Task ID

        Returns:
            CommitResult with commit SHA and details

        Example:
            >>> result = client.git.commit_unstaged(
            ...     instance_url="http://localhost:8102",
            ...     task_id=154
            ... )
            >>> if result.success:
            ...     print(f"Committed {result.files_committed} files")
            ...     print(f"SHA: {result.commit_sha}")
        """
        params = {"task_id": task_id}
        url = f"{instance_url}/api/claude/commit-unstaged"
        data = self.http.post(url, params=params)
        return CommitResult(**data)

    def push(
        self,
        instance_url: str,
        task_id: int,
        branch: Optional[str] = None,
        force: bool = False,
    ) -> PushResult:
        """
        Push committed changes to remote repository.

        Args:
            instance_url: Instance URL
            task_id: Task ID
            branch: Branch to push (optional, uses current branch if not specified)
            force: Whether to force push

        Returns:
            PushResult with push status

        Example:
            >>> result = client.git.push(
            ...     instance_url="http://localhost:8102",
            ...     task_id=154
            ... )
            >>> if result.success:
            ...     print(f"Pushed {result.pushed_commits} commits to {result.branch}")
        """
        params = {"task_id": task_id}
        request_data = {}
        if branch:
            request_data["branch"] = branch
        if force:
            request_data["force"] = force

        url = f"{instance_url}/api/git/push"
        data = self.http.post(url, data=request_data if request_data else None, params=params)
        return PushResult(**data)
