"""
Dependency injection composer for instance module.

This composer follows the same pattern as core and repository modules,
centralizing dependency creation and configuration with correct constructor signatures.
"""

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.core.infrastructure.driving_adapter.cli.composer import CoreComposer
from dooservice.instance.application.use_cases.create_instance import CreateInstance
from dooservice.instance.application.use_cases.delete_instance import DeleteInstance
from dooservice.instance.application.use_cases.exec_instance import ExecInstance
from dooservice.instance.application.use_cases.list_instances import ListInstances
from dooservice.instance.application.use_cases.logs_instance import LogsInstance
from dooservice.instance.application.use_cases.restart_instance import RestartInstance
from dooservice.instance.application.use_cases.start_instance import StartInstance
from dooservice.instance.application.use_cases.status_instance import StatusInstance
from dooservice.instance.application.use_cases.stop_instance import StopInstance
from dooservice.instance.application.use_cases.sync_instance import SyncInstance
from dooservice.instance.application.use_cases.update_odoo_modules import (
    UpdateOdooModules,
)
from dooservice.instance.domain.services.docker_orchestrator import DockerOrchestrator
from dooservice.instance.domain.services.instance_orchestrator import (
    InstanceOrchestrator,
)
from dooservice.instance.domain.services.instance_validator import InstanceValidator
from dooservice.instance.infrastructure.driven_adapter.docker_client_adapter import (
    DockerClientAdapter,
)
from dooservice.instance.infrastructure.driven_adapter.filesystem_instance_adapter import (  # noqa: E501
    FilesystemInstanceAdapter,
)
from dooservice.repository.infrastructure.driving_adapter.cli.composer import (
    RepositoryComposer,
)
from dooservice.shared.messaging import ClickMessenger


class InstanceComposer:
    """Dependency injection composer for instance module."""

    def __init__(self, config_path: str = "dooservice.yml"):
        self._config_path = config_path
        self._core_composer = CoreComposer()
        self._repository_composer = RepositoryComposer(config_path)
        self._message_interface = None
        self._docker_adapter = None
        self._filesystem_adapter = None
        self._instance_orchestrator = None
        self._docker_orchestrator = None
        self._configuration = None
        self._instance_validator = None

    @property
    def message_interface(self) -> ClickMessenger:
        """Get message interface implementation."""
        if self._message_interface is None:
            self._message_interface = ClickMessenger()
        return self._message_interface

    @property
    def docker_adapter(self) -> DockerClientAdapter:
        """Get Docker client adapter."""
        if self._docker_adapter is None:
            self._docker_adapter = DockerClientAdapter()
        return self._docker_adapter

    @property
    def filesystem_adapter(self) -> FilesystemInstanceAdapter:
        """Get filesystem adapter."""
        if self._filesystem_adapter is None:
            self._filesystem_adapter = FilesystemInstanceAdapter(self.docker_adapter)
        return self._filesystem_adapter

    @property
    def instance_orchestrator(self) -> InstanceOrchestrator:
        """Get instance orchestrator."""
        if self._instance_orchestrator is None:
            self._instance_orchestrator = InstanceOrchestrator()
        return self._instance_orchestrator

    @property
    def docker_orchestrator(self) -> DockerOrchestrator:
        """Get Docker orchestrator."""
        if self._docker_orchestrator is None:
            self._docker_orchestrator = DockerOrchestrator()
        return self._docker_orchestrator

    @property
    def instance_validator(self) -> InstanceValidator:
        """Get instance validator domain service."""
        if self._instance_validator is None:
            self._instance_validator = InstanceValidator()
        return self._instance_validator

    def get_configuration(self) -> DooServiceConfiguration:
        """Load configuration once and cache it."""
        if self._configuration is None:
            load_config_use_case = self._core_composer.get_load_configuration_use_case()
            self._configuration = load_config_use_case.execute(self._config_path)
        return self._configuration

    def get_create_instance_use_case(self) -> CreateInstance:
        """Get create instance use case."""
        sync_repositories_use_case = (
            self._repository_composer.get_sync_repositories_use_case()
        )
        return CreateInstance(
            sync_repositories=sync_repositories_use_case,
            instance_repository=self.filesystem_adapter,
            docker_repository=self.docker_adapter,
            instance_orchestrator=self.instance_orchestrator,
            docker_orchestrator=self.docker_orchestrator,
            messenger=self.message_interface,
        )

    @property
    def delete_instance_use_case(self) -> DeleteInstance:
        """Get delete instance use case."""
        return DeleteInstance(
            instance_repository=self.filesystem_adapter,
            docker_repository=self.docker_adapter,
            messenger=self.message_interface,
        )

    @property
    def start_instance_use_case(self) -> StartInstance:
        """Get start instance use case."""
        return StartInstance(
            instance_repository=self.filesystem_adapter,
            docker_repository=self.docker_adapter,
            messenger=self.message_interface,
        )

    @property
    def stop_instance_use_case(self) -> StopInstance:
        """Get stop instance use case."""
        return StopInstance(
            instance_repository=self.filesystem_adapter,
            docker_repository=self.docker_adapter,
            messenger=self.message_interface,
        )

    @property
    def status_instance_use_case(self) -> StatusInstance:
        """Get status instance use case."""
        return StatusInstance(
            instance_repository=self.filesystem_adapter,
            messenger=self.message_interface,
        )

    @property
    def logs_instance_use_case(self) -> LogsInstance:
        """Get logs instance use case."""
        return LogsInstance(
            instance_repository=self.filesystem_adapter,
            docker_repository=self.docker_adapter,
            messenger=self.message_interface,
        )

    @property
    def exec_instance_use_case(self) -> ExecInstance:
        """Get exec instance use case."""
        return ExecInstance(
            instance_repository=self.filesystem_adapter,
            docker_repository=self.docker_adapter,
            messenger=self.message_interface,
        )

    def get_sync_instance_use_case(self) -> SyncInstance:
        """Get sync instance use case."""
        sync_repositories_use_case = (
            self._repository_composer.get_sync_repositories_use_case()
        )
        return SyncInstance(
            sync_repositories=sync_repositories_use_case,
            instance_repository=self.filesystem_adapter,
            docker_repository=self.docker_adapter,
            instance_orchestrator=self.instance_orchestrator,
            messenger=self.message_interface,
        )

    @property
    def restart_instance_use_case(self) -> RestartInstance:
        """Get restart instance use case."""
        return RestartInstance(
            stop_instance=self.stop_instance_use_case,
            start_instance=self.start_instance_use_case,
            messenger=self.message_interface,
        )

    @property
    def update_odoo_modules_use_case(self) -> UpdateOdooModules:
        """Get update Odoo modules use case."""
        return UpdateOdooModules(
            instance_repository=self.filesystem_adapter,
            docker_repository=self.docker_adapter,
            messenger=self.message_interface,
        )

    @property
    def list_instances_use_case(self) -> ListInstances:
        """Get list instances use case."""
        return ListInstances(
            instance_repository=self.filesystem_adapter,
            messenger=self.message_interface,
        )
