from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from dooservice.core.domain.entities.configuration import Repository


class RepositoryConfigurationRepository(ABC):
    """Abstract repository for accessing repository configuration."""

    @abstractmethod
    def get_global_repositories(self) -> Dict[str, Repository]:
        """Get all globally configured repositories."""
        raise NotImplementedError()

    @abstractmethod
    def get_instance_repositories(self, instance_name: str) -> Dict[str, Repository]:
        """Get repositories configured for a specific instance."""
        raise NotImplementedError()

    @abstractmethod
    def get_all_repositories_for_instance(
        self, instance_name: str
    ) -> Dict[str, Repository]:
        """Get all repositories available to an instance.

        Returns global + instance-specific repositories.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_repository_by_name(
        self, repo_name: str, instance_name: Optional[str] = None
    ) -> Optional[Repository]:
        """Get a specific repository by name."""
        raise NotImplementedError()

    @abstractmethod
    def instance_exists(self, instance_name: str) -> bool:
        """Check if an instance exists in configuration."""
        raise NotImplementedError()

    @abstractmethod
    def get_all_instance_names(self) -> List[str]:
        """Get all instance names from configuration."""
        raise NotImplementedError()
