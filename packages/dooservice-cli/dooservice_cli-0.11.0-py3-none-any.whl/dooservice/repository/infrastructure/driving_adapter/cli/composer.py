from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.core.infrastructure.driving_adapter.cli.composer import CoreComposer
from dooservice.repository.application.use_cases.get_repository_status import (
    GetRepositoryStatusUseCase,
)
from dooservice.repository.application.use_cases.list_repositories import (
    ListRepositoriesUseCase,
)
from dooservice.repository.application.use_cases.sync_repositories import (
    SyncRepositoriesUseCase,
)
from dooservice.repository.infrastructure.driven_adapter.git_python_adapter import (
    GitPythonAdapter,
)
from dooservice.repository.infrastructure.implementation.configuration_repository_impl import (  # noqa: E501
    ConfigurationRepositoryImpl,
)
from dooservice.repository.infrastructure.implementation.repository_manager_impl import (  # noqa: E501
    RepositoryManagerImpl,
)
from dooservice.shared.messaging import ClickMessenger


class RepositoryComposer:
    """Dependency injection composer for repository module."""

    def __init__(self, config_path: str = "dooservice.yml"):
        self._config_path = config_path
        self._core_composer = CoreComposer()
        self._git_repository = None
        self._config_repository = None
        self._repository_manager = None
        self._message_interface = None
        self._configuration = None

    @property
    def git_repository(self) -> GitPythonAdapter:
        """Get Git repository implementation."""
        if self._git_repository is None:
            self._git_repository = GitPythonAdapter()
        return self._git_repository

    def get_configuration(self) -> DooServiceConfiguration:
        """Load configuration once and cache it."""
        if self._configuration is None:
            load_config_use_case = self._core_composer.get_load_configuration_use_case()
            self._configuration = load_config_use_case.execute(self._config_path)
        return self._configuration

    def get_config_repository(self) -> ConfigurationRepositoryImpl:
        """Get configuration repository implementation."""
        if self._config_repository is None:
            config = self.get_configuration()
            self._config_repository = ConfigurationRepositoryImpl(config)
        return self._config_repository

    @property
    def message_interface(self) -> ClickMessenger:
        """Get message interface implementation."""
        if self._message_interface is None:
            self._message_interface = ClickMessenger()
        return self._message_interface

    def get_repository_manager(self) -> RepositoryManagerImpl:
        """Get repository manager implementation."""
        if self._repository_manager is None:
            config_repo = self.get_config_repository()
            self._repository_manager = RepositoryManagerImpl(
                git_repository=self.git_repository,
                config_repository=config_repo,
                message_interface=self.message_interface,
            )
        return self._repository_manager

    def get_list_repositories_use_case(self) -> ListRepositoriesUseCase:
        """Get list repositories use case."""
        repo_manager = self.get_repository_manager()
        return ListRepositoriesUseCase(repo_manager)

    def get_repository_status_use_case(self) -> GetRepositoryStatusUseCase:
        """Get repository status use case."""
        repo_manager = self.get_repository_manager()
        return GetRepositoryStatusUseCase(repo_manager)

    def get_sync_repositories_use_case(self) -> SyncRepositoriesUseCase:
        """Get sync repositories use case."""
        repo_manager = self.get_repository_manager()
        return SyncRepositoriesUseCase(repo_manager)
