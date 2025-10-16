from typing import List, Optional

from dooservice.repository.domain.entities.repository_info import RepositoryInfo
from dooservice.repository.domain.exceptions.repository_exceptions import (
    RepositoryNotFoundError,
)
from dooservice.repository.domain.services.repository_manager import RepositoryManager


class ListRepositoriesUseCase:
    """Use case for listing repositories of an instance."""

    def __init__(self, repository_manager: RepositoryManager):
        self._repository_manager = repository_manager

    async def execute(
        self, instance_name: str, repo_name: Optional[str] = None
    ) -> List[RepositoryInfo]:
        """
        List repositories for a specific instance.

        Args:
            instance_name: Name of the instance
            repo_name: Optional specific repository name to filter

        Returns:
            List of repository information

        Raises:
            RepositoryNotFoundError: If instance or repository not found
        """
        try:
            return await self._repository_manager.list_repositories(
                instance_name, repo_name
            )
        except Exception as e:
            raise RepositoryNotFoundError(
                f"Error listing repositories for instance '{instance_name}': {str(e)}"
            ) from e
