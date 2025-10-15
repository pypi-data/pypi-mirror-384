from abc import ABC, abstractmethod
from typing import Optional

from dooservice.repository.domain.entities.repository_info import RepositoryInfo
from dooservice.repository.domain.entities.sync_result import SyncResult


class GitRepository(ABC):
    """Abstract repository for Git operations."""

    @abstractmethod
    def get_repository_status(
        self, repo_path: str, repo_url: str, repo_branch: str
    ) -> RepositoryInfo:
        """Get the status of a repository."""
        raise NotImplementedError()

    @abstractmethod
    def clone_repository(
        self,
        repo_url: str,
        repo_path: str,
        repo_branch: str,
        ssh_key_path: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> bool:
        """Clone a repository."""
        raise NotImplementedError()

    @abstractmethod
    def pull_repository(self, repo_path: str, repo_branch: str) -> bool:
        """Pull latest changes from repository."""
        raise NotImplementedError()

    @abstractmethod
    def sync_repository(
        self,
        repo_url: str,
        repo_path: str,
        repo_branch: str,
        include_submodules: bool = False,
        ssh_key_path: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> SyncResult:
        """Synchronize repository (clone if needed, pull if exists)."""
        raise NotImplementedError()

    @abstractmethod
    def update_submodules(self, repo_path: str) -> bool:
        """Update repository submodules."""
        raise NotImplementedError()

    @abstractmethod
    def is_repository_cloned(self, repo_path: str) -> bool:
        """Check if repository is already cloned."""
        raise NotImplementedError()
