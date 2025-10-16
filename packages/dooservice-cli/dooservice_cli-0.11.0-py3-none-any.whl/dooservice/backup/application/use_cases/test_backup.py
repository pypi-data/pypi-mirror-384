"""Simplified test backup use case."""

from pathlib import Path
from typing import Any, Dict

from dooservice.backup.domain.entities.backup_configuration import BackupConfiguration
from dooservice.backup.domain.exceptions.backup_exceptions import (
    BackupConfigurationError,
    BackupExecutionError,
)
from dooservice.backup.domain.services.backup_executor import BackupExecutor
from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.shared.messaging import MessageInterface


class TestBackup:
    """Simplified backup test use case."""

    def __init__(self, backup_executor: BackupExecutor, messenger: MessageInterface):
        self._backup_executor = backup_executor
        self._messenger = messenger

    async def execute(
        self,
        instance_name: str,
        configuration: DooServiceConfiguration,
        database_name: str = "test",
    ) -> Dict[str, Any]:
        """Test backup connection."""
        try:
            self._messenger.send_info(f"Testing backup for instance: {instance_name}")

            # Validate instance exists
            if instance_name not in configuration.instances:
                raise BackupConfigurationError(f"Instance '{instance_name}' not found")

            instance_config = configuration.instances[instance_name]
            admin_password = getattr(instance_config.env_vars, "ADMIN_PASSWORD", None)
            if not admin_password:
                raise BackupConfigurationError("ADMIN_PASSWORD not found")

            # Create simple test configuration
            backup_config = BackupConfiguration(
                admin_password=admin_password,
                database_name=database_name,
                output_path=Path("/tmp"),  # noqa: S108
                backup_format="zip",
            )

            # Test connection
            test_result = await self._backup_executor.test_connection(
                instance_name=instance_name, backup_config=backup_config
            )

            if test_result.get("success"):
                self._messenger.send_success("Backup test successful")
            else:
                self._messenger.send_warning(f"Test failed: {test_result.get('error')}")

            return test_result

        except (BackupConfigurationError, BackupExecutionError):
            raise
        except Exception as e:
            error_msg = f"Test failed: {e}"
            self._messenger.send_error(error_msg)
            raise BackupExecutionError(error_msg) from e
