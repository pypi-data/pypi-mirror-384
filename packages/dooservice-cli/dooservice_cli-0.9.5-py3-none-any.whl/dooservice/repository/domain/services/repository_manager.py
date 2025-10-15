from abc import ABC, abstractmethod
from typing import List, Optional

from dooservice.repository.domain.entities.repository_info import RepositoryInfo
from dooservice.repository.domain.entities.sync_result import SyncResult


class RepositoryManager(ABC):
    """Domain service for repository management operations."""

    @abstractmethod
    async def list_repositories(
        self, instance_name: str, repo_name: Optional[str] = None
    ) -> List[RepositoryInfo]:
        """List repositories for an instance."""
        raise NotImplementedError()

    @abstractmethod
    async def get_repository_status(
        self, instance_name: str, repo_name: str
    ) -> RepositoryInfo:
        """Get status of a specific repository."""
        raise NotImplementedError()

    @abstractmethod
    async def sync_repositories(
        self,
        instance_name: str,
        repo_name: Optional[str] = None,
        test_mode: bool = False,
    ) -> List[SyncResult]:
        """Sync repositories for an instance."""
        raise NotImplementedError()
