from dooservice.core.infrastructure.implementation.configuration_manager import (
    ConfigurationManager,
)
from dooservice.instance.application.use_cases.create_instance import CreateInstance
from dooservice.instance.application.use_cases.delete_instance import DeleteInstance
from dooservice.instance.application.use_cases.exec_instance import ExecInstance
from dooservice.instance.application.use_cases.logs_instance import LogsInstance
from dooservice.instance.application.use_cases.start_instance import StartInstance
from dooservice.instance.application.use_cases.status_instance import StatusInstance
from dooservice.instance.application.use_cases.stop_instance import StopInstance
from dooservice.instance.application.use_cases.sync_instance import SyncInstance
from dooservice.instance.application.use_cases.sync_repositories_wrapper import (
    SyncRepositories,
)
from dooservice.instance.domain.services.docker_orchestrator import DockerOrchestrator
from dooservice.instance.domain.services.instance_orchestrator import (
    InstanceOrchestrator,
)
from dooservice.instance.infrastructure.driven_adapter.docker_client_adapter import (
    DockerClientAdapter,
)
from dooservice.instance.infrastructure.driven_adapter.filesystem_instance_adapter import (  # noqa: E501
    FilesystemInstanceAdapter,
)
from dooservice.repository.infrastructure.driving_adapter.cli.composer import (
    RepositoryComposer,
)
from dooservice.shared.messaging import MessageInterface


class InstanceManager:
    """Instance management implementation that coordinates all dependencies."""

    def __init__(self, messenger: MessageInterface):
        self._messenger = messenger

        self._docker_adapter = DockerClientAdapter()
        self._instance_adapter = FilesystemInstanceAdapter(self._docker_adapter)

        config_manager = ConfigurationManager(messenger)
        repo_composer = RepositoryComposer()

        self._load_configuration = config_manager.get_load_configuration_use_case()
        self._sync_repositories = SyncRepositories(
            repo_composer.sync_repositories_use_case
        )

        self._instance_orchestrator = InstanceOrchestrator()
        self._docker_orchestrator = DockerOrchestrator()

    def get_create_instance_use_case(self) -> CreateInstance:
        """Get the create instance use case."""
        return CreateInstance(
            self._load_configuration,
            self._sync_repositories,
            self._instance_adapter,
            self._docker_adapter,
            self._instance_orchestrator,
            self._docker_orchestrator,
            self._messenger,
        )

    def get_delete_instance_use_case(self) -> DeleteInstance:
        """Get the delete instance use case."""
        return DeleteInstance(
            self._load_configuration,
            self._instance_adapter,
            self._docker_adapter,
            self._messenger,
        )

    def get_start_instance_use_case(self) -> StartInstance:
        """Get the start instance use case."""
        return StartInstance(
            self._instance_adapter, self._docker_adapter, self._messenger
        )

    def get_stop_instance_use_case(self) -> StopInstance:
        """Get the stop instance use case."""
        return StopInstance(
            self._instance_adapter, self._docker_adapter, self._messenger
        )

    def get_status_instance_use_case(self) -> StatusInstance:
        """Get the status instance use case."""
        return StatusInstance(self._instance_adapter, self._messenger)

    def get_logs_instance_use_case(self) -> LogsInstance:
        """Get the logs instance use case."""
        return LogsInstance(
            self._instance_adapter, self._docker_adapter, self._messenger
        )

    def get_exec_instance_use_case(self) -> ExecInstance:
        """Get the exec instance use case."""
        return ExecInstance(
            self._instance_adapter, self._docker_adapter, self._messenger
        )

    def get_sync_instance_use_case(self) -> SyncInstance:
        """Get the sync instance use case."""
        return SyncInstance(
            self._load_configuration,
            self._sync_repositories,
            self._instance_adapter,
            self._docker_adapter,
            self._instance_orchestrator,
            self._messenger,
        )
