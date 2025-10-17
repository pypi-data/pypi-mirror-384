"""
Git operation models for the NetInt API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class GitFile(BaseModel):
    """
    Represents a changed file in git.

    Attributes:
        path: File path
        status: Change status (added, modified, deleted)
        additions: Number of lines added
        deletions: Number of lines deleted
        patch: Git patch/diff content (if requested)
    """

    path: str
    status: str
    additions: int = 0
    deletions: int = 0
    patch: Optional[str] = None


class GitRepository(BaseModel):
    """
    Git repository information.

    Attributes:
        name: Repository name
        path: Repository path
        branch: Current branch
        current_commit: Current commit SHA
    """

    name: str
    path: str
    branch: str
    current_commit: str


class GitChangeSummary(BaseModel):
    """
    Summary of git changes.

    Attributes:
        total_files: Total number of changed files
        additions: Total lines added
        deletions: Total lines deleted
        files: List of changed files
    """

    total_files: int
    additions: int
    deletions: int
    files: List[GitFile]


class GitChanges(BaseModel):
    """
    Complete git changes information.

    Attributes:
        repository: Repository information
        changes: Change summary
        task_id: Associated task ID
    """

    repository: GitRepository
    changes: GitChangeSummary
    task_id: Optional[int] = None


class GitStatusFile(BaseModel):
    """
    File status in git.

    Attributes:
        path: File path
        status: Status code (A=added, M=modified, D=deleted, etc.)
    """

    path: str
    status: str


class GitStatus(BaseModel):
    """
    Git repository status.

    Attributes:
        branch: Current branch
        ahead: Commits ahead of remote
        behind: Commits behind remote
        staged: Staged files
        unstaged: Unstaged files
        untracked: Untracked files
        clean: Whether working directory is clean
        task_id: Associated task ID
    """

    branch: str
    ahead: int = 0
    behind: int = 0
    staged: List[GitStatusFile] = []
    unstaged: List[GitStatusFile] = []
    untracked: List[str] = []
    clean: bool = True
    task_id: Optional[int] = None


class CommitResult(BaseModel):
    """
    Result of a git commit operation.

    Attributes:
        success: Whether commit succeeded
        commit_sha: Commit SHA
        message: Commit message
        files_committed: Number of files committed
        task_id: Associated task ID
    """

    success: bool
    commit_sha: Optional[str] = None
    message: str
    files_committed: int = 0
    task_id: Optional[int] = None


class PushResult(BaseModel):
    """
    Result of a git push operation.

    Attributes:
        success: Whether push succeeded
        branch: Branch name
        pushed_commits: Number of commits pushed
        message: Result message
        task_id: Associated task ID
    """

    success: bool
    branch: str
    pushed_commits: int = 0
    message: str
    task_id: Optional[int] = None
