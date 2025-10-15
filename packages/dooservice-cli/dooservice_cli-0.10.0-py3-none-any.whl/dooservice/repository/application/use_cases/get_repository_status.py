from dooservice.repository.domain.entities.repository_info import RepositoryInfo
from dooservice.repository.domain.exceptions.repository_exceptions import (
    RepositoryNotFoundError,
    RepositoryStatusError,
)
from dooservice.repository.domain.services.repository_manager import RepositoryManager


class GetRepositoryStatusUseCase:
    """Use case for getting detailed status of a repository."""

    def __init__(self, repository_manager: RepositoryManager):
        self._repository_manager = repository_manager

    async def execute(self, instance_name: str, repo_name: str) -> RepositoryInfo:
        """
        Get detailed status of a specific repository.

        Args:
            instance_name: Name of the instance
            repo_name: Name of the repository

        Returns:
            Repository information with detailed status

        Raises:
            RepositoryNotFoundError: If instance or repository not found
            RepositoryStatusError: If error checking repository status
        """
        try:
            return await self._repository_manager.get_repository_status(
                instance_name, repo_name
            )
        except RepositoryNotFoundError:
            raise
        except Exception as e:
            raise RepositoryStatusError(
                f"Error getting status for repository '{repo_name}' "
                f"in instance '{instance_name}': {str(e)}"
            ) from e
