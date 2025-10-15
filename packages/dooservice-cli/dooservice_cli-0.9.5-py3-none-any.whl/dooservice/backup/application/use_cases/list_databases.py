"""Simplified list databases use case."""

from pathlib import Path
from typing import List

from dooservice.backup.domain.entities.backup_configuration import BackupConfiguration
from dooservice.backup.domain.exceptions.backup_exceptions import (
    BackupConfigurationError,
    BackupExecutionError,
)
from dooservice.backup.domain.services.backup_executor import BackupExecutor
from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.shared.messaging import MessageInterface


class ListDatabases:
    """Simplified list databases use case."""

    def __init__(self, backup_executor: BackupExecutor, messenger: MessageInterface):
        self._backup_executor = backup_executor
        self._messenger = messenger

    async def execute(
        self, instance_name: str, configuration: DooServiceConfiguration
    ) -> List[str]:
        """List available databases."""
        try:
            self._messenger.send_info(
                f"Listing databases for instance: {instance_name}"
            )

            # Validate instance exists
            if instance_name not in configuration.instances:
                raise BackupConfigurationError(f"Instance '{instance_name}' not found")

            instance_config = configuration.instances[instance_name]
            admin_password = getattr(instance_config.env_vars, "ADMIN_PASSWORD", None)
            if not admin_password:
                raise BackupConfigurationError("ADMIN_PASSWORD not found")

            # Create minimal configuration for listing
            backup_config = BackupConfiguration(
                admin_password=admin_password,
                database_name="dummy",  # Not used for listing
                output_path=Path("/tmp"),  # Not used for listing  # noqa: S108
                backup_format="zip",
            )

            # List databases
            databases = await self._backup_executor.list_databases(
                instance_name=instance_name, backup_config=backup_config
            )

            self._messenger.send_success(f"Found {len(databases)} databases")
            return databases

        except (BackupConfigurationError, BackupExecutionError):
            raise
        except Exception as e:
            error_msg = f"Failed to list databases: {e}"
            self._messenger.send_error(error_msg)
            raise BackupExecutionError(error_msg) from e
