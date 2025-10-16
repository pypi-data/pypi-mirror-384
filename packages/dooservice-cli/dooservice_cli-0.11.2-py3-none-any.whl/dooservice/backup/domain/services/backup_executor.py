"""
Backup executor service interface.

This service handles backup operations using XML-RPC with automatic instance detection.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from dooservice.backup.domain.entities.backup_configuration import BackupConfiguration
from dooservice.backup.domain.entities.backup_metadata import BackupMetadata


class BackupExecutor(ABC):
    """
    Abstract interface for backup executor.

    This service executes backups using XML-RPC with automatic instance detection.
    """

    @abstractmethod
    async def execute_backup(
        self,
        instance_name: str,
        backup_config: BackupConfiguration,
        output_path: Optional[Path] = None,
    ) -> BackupMetadata:
        """
        Execute a backup using XML-RPC API with automatic instance detection.

        Args:
            instance_name: Name of the instance
            backup_config: Configuration containing all backup settings
            output_path: Optional output path override

        Returns:
            BackupMetadata with information about the created backup

        Raises:
            BackupExecutionError: If backup fails
            BackupConfigurationError: If configuration is invalid
        """

    @abstractmethod
    async def test_connection(
        self, instance_name: str, backup_config: BackupConfiguration
    ) -> Dict[str, Any]:
        """
        Test connection to Odoo server using XML-RPC with automatic detection.

        Args:
            instance_name: Name of the instance
            backup_config: Configuration containing all backup settings

        Returns:
            Dictionary with connection test results

        Raises:
            BackupConfigurationError: If connection test fails
        """

    @abstractmethod
    async def list_databases(
        self, instance_name: str, backup_config: BackupConfiguration
    ) -> List[str]:
        """
        List available databases on the Odoo server.

        Args:
            instance_name: Name of the instance
            backup_config: Configuration containing all backup settings

        Returns:
            List of database names

        Raises:
            BackupConfigurationError: If unable to list databases
        """
