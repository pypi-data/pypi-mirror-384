"""Simplified create backup use case."""

from pathlib import Path
from typing import Optional

from dooservice.backup.domain.entities.backup_configuration import BackupConfiguration
from dooservice.backup.domain.entities.backup_metadata import BackupMetadata
from dooservice.backup.domain.exceptions.backup_exceptions import (
    BackupConfigurationError,
    BackupExecutionError,
)
from dooservice.backup.domain.services.backup_executor import BackupExecutor
from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.shared.messaging import MessageInterface


class CreateBackup:
    """Simplified backup creation use case."""

    def __init__(self, backup_executor: BackupExecutor, messenger: MessageInterface):
        self._backup_executor = backup_executor
        self._messenger = messenger

    async def execute(
        self,
        instance_name: str,
        configuration: DooServiceConfiguration,
        database_name: str,
        output_path: Optional[Path] = None,
        output_format: str = "zip",
    ) -> BackupMetadata:
        """Execute backup creation."""
        try:
            self._messenger.send_info(f"Starting backup for instance: {instance_name}")

            # Validate instance exists
            if instance_name not in configuration.instances:
                raise BackupConfigurationError(f"Instance '{instance_name}' not found")

            instance_config = configuration.instances[instance_name]

            # Get admin password from env vars
            admin_password = getattr(instance_config.env_vars, "ADMIN_PASSWORD", None)
            if not admin_password:
                raise BackupConfigurationError(
                    "ADMIN_PASSWORD not found in instance env_vars"
                )

            # Create simple backup configuration
            backup_config = BackupConfiguration(
                admin_password=admin_password,
                database_name=database_name,
                output_path=(
                    output_path or Path(configuration.backup.output_dir) / instance_name
                ),
                backup_format=output_format,
            )

            # Execute backup
            metadata = await self._backup_executor.execute_backup(
                instance_name=instance_name,
                backup_config=backup_config,
                output_path=output_path,
            )

            self._messenger.send_success(f"Backup completed: {metadata.file_path}")
            return metadata

        except (BackupConfigurationError, BackupExecutionError):
            raise
        except Exception as e:
            error_msg = f"Backup failed: {e}"
            self._messenger.send_error(error_msg)
            raise BackupExecutionError(error_msg) from e
