"""
Dependency injection composer for backup module.

This composer follows the same pattern as core, instance and repository modules,
centralizing dependency creation and configuration.
"""

from dooservice.backup.application.use_cases.create_backup import CreateBackup
from dooservice.backup.application.use_cases.list_databases import ListDatabases
from dooservice.backup.application.use_cases.test_backup import TestBackup
from dooservice.backup.infrastructure.implementation.xmlrpc_backup_executor import (
    XMLRPCBackupExecutor,
)
from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.core.infrastructure.driving_adapter.cli.composer import CoreComposer
from dooservice.instance.infrastructure.driven_adapter.docker_client_adapter import (
    DockerClientAdapter,
)
from dooservice.shared.messaging import ClickMessenger


class BackupComposer:
    """Dependency injection composer for backup module."""

    def __init__(self, config_path: str = "dooservice.yml"):
        self._config_path = config_path
        self._core_composer = CoreComposer()
        self._message_interface = None
        self._docker_adapter = None
        self._backup_executor = None
        self._config = None

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
    def backup_executor(self) -> XMLRPCBackupExecutor:
        """Get backup executor implementation."""
        if self._backup_executor is None:
            self._backup_executor = XMLRPCBackupExecutor(self.docker_adapter)
        return self._backup_executor

    def get_configuration(self) -> DooServiceConfiguration:
        """Load configuration once and cache it."""
        if self._config is None:
            load_config_use_case = self._core_composer.get_load_configuration_use_case()
            self._config = load_config_use_case.execute(self._config_path)
        return self._config

    def get_create_backup_use_case(self) -> CreateBackup:
        """Get create backup use case."""
        return CreateBackup(
            backup_executor=self.backup_executor, messenger=self.message_interface
        )

    def get_test_backup_use_case(self) -> TestBackup:
        """Get test backup use case."""
        return TestBackup(
            backup_executor=self.backup_executor, messenger=self.message_interface
        )

    def get_list_databases_use_case(self) -> ListDatabases:
        """Get list databases use case."""
        return ListDatabases(
            backup_executor=self.backup_executor, messenger=self.message_interface
        )
