from typing import List, Optional

from dooservice.repository.domain.entities.sync_result import SyncResult
from dooservice.repository.domain.exceptions.repository_exceptions import (
    RepositoryNotFoundError,
    RepositorySyncError,
)
from dooservice.repository.domain.services.repository_manager import RepositoryManager


class SyncRepositoriesUseCase:
    """Use case for synchronizing repositories."""

    def __init__(self, repository_manager: RepositoryManager):
        self._repository_manager = repository_manager

    async def execute(
        self,
        instance_name: str,
        repo_name: Optional[str] = None,
        test_mode: bool = False,
    ) -> List[SyncResult]:
        """
        Synchronize repositories for an instance.

        Args:
            instance_name: Name of the instance
            repo_name: Optional specific repository name to sync
            test_mode: If True, use test directory for cloning

        Returns:
            List of synchronization results

        Raises:
            RepositoryNotFoundError: If instance or repository not found
            RepositorySyncError: If error during synchronization
        """
        try:
            return await self._repository_manager.sync_repositories(
                instance_name, repo_name, test_mode
            )
        except RepositoryNotFoundError:
            raise
        except Exception as e:
            target = f"repository '{repo_name}'" if repo_name else "repositories"
            raise RepositorySyncError(
                f"Error syncing {target} for instance '{instance_name}': {str(e)}"
            ) from e
