"""Simplified XML-RPC backup executor."""

import base64
from datetime import datetime
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from dooservice.backup.domain.entities.backup_configuration import BackupConfiguration
from dooservice.backup.domain.entities.backup_metadata import BackupMetadata
from dooservice.backup.domain.exceptions.backup_exceptions import (
    BackupExecutionError,
)
from dooservice.backup.domain.services.backup_executor import BackupExecutor
from dooservice.instance.domain.repositories.docker_repository import DockerRepository


class XMLRPCBackupExecutor(BackupExecutor):
    """Simplified XML-RPC backup executor."""

    def __init__(self, docker_repository: DockerRepository):
        self._docker_repository = docker_repository

    async def execute_backup(
        self,
        instance_name: str,
        backup_config: BackupConfiguration,
        output_path: Optional[Path] = None,
    ) -> BackupMetadata:
        """Execute backup using XML-RPC."""
        # Validate instance is running
        instance_info = await self._docker_repository.get_instance_containers(
            instance_name
        )
        if not instance_info or not instance_info.is_running():
            raise BackupExecutionError(f"Instance '{instance_name}' is not running")

        # Setup output path
        output_path = output_path or backup_config.output_path
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = (
            f"{backup_config.database_name}_{timestamp}.{backup_config.backup_format}"
        )
        backup_filepath = output_path / backup_filename

        # Execute backup
        backup_data = await self._execute_backup_command(instance_name, backup_config)

        # Save and create metadata
        backup_filepath.write_bytes(backup_data)
        checksum = hashlib.sha256(backup_data).hexdigest()

        return BackupMetadata(
            backup_id=f"{instance_name}_{timestamp}",
            instance_name=instance_name,
            database_name=backup_config.database_name,
            created_at=datetime.now(),
            file_path=str(backup_filepath),
            file_size=len(backup_data),
            database_included=True,
            filestore_included=True,
            compressed=True,
            checksum=checksum,
            backup_format=backup_config.backup_format,
        )

    async def _execute_backup_command(
        self,
        instance_name: str,
        backup_config: BackupConfiguration,
    ) -> bytes:
        """Execute XML-RPC backup command in container."""
        backup_script = f'''
import xmlrpc.client
import base64
import sys

try:
    db_proxy = xmlrpc.client.ServerProxy("http://localhost:8069/xmlrpc/2/db")
    backup_b64 = db_proxy.dump(
        "{backup_config.admin_password}",
        "{backup_config.database_name}",
        "{backup_config.backup_format}"
    )
    print(backup_b64)
except Exception as e:
    print(f"ERROR: {{e}}", file=sys.stderr)
    sys.exit(1)
'''
        container_name = f"web_{instance_name}"
        command = ["python3", "-c", backup_script]

        try:
            output = await self._docker_repository.execute_command(
                container_name, command
            )
            return base64.b64decode(output.strip())
        except Exception as e:
            raise BackupExecutionError(f"Backup failed: {e}") from e

    async def test_connection(
        self, instance_name: str, backup_config: BackupConfiguration
    ) -> Dict[str, Any]:
        """Simple connection test."""
        try:
            instance_info = await self._docker_repository.get_instance_containers(
                instance_name
            )
            if not instance_info or not instance_info.is_running():
                return {
                    "success": False,
                    "error": f"Instance '{instance_name}' is not running",
                }

            # Simple test script
            test_script = """
import xmlrpc.client
try:
    common = xmlrpc.client.ServerProxy("http://localhost:8069/xmlrpc/2/common")
    version_info = common.version()
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
"""
            container_name = f"web_{instance_name}"
            command = ["python3", "-c", test_script]
            output = await self._docker_repository.execute_command(
                container_name, command
            )

            return {"success": output.strip() == "SUCCESS", "output": output.strip()}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": str(e)}

    async def list_databases(
        self, instance_name: str, backup_config: BackupConfiguration
    ) -> List[str]:
        """List databases."""
        try:
            instance_info = await self._docker_repository.get_instance_containers(
                instance_name
            )
            if not instance_info or not instance_info.is_running():
                raise BackupExecutionError(f"Instance '{instance_name}' is not running")

            list_script = """
import xmlrpc.client
try:
    db_proxy = xmlrpc.client.ServerProxy("http://localhost:8069/xmlrpc/2/db")
    db_list = db_proxy.list()
    for db in db_list:
        print(db)
except Exception as e:
    print(f"ERROR: {e}")
"""
            container_name = f"web_{instance_name}"
            command = ["python3", "-c", list_script]
            output = await self._docker_repository.execute_command(
                container_name, command
            )

            lines = output.strip().split("\n")
            if lines and lines[0].startswith("ERROR:"):
                raise BackupExecutionError(f"Database listing failed: {lines[0]}")
            return [line for line in lines if line and not line.startswith("ERROR:")]
        except Exception as e:
            raise BackupExecutionError(f"Failed to list databases: {e}") from e
