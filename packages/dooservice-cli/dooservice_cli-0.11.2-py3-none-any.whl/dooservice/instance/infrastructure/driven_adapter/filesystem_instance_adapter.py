from pathlib import Path
import shutil
from typing import List, Optional

from dooservice.instance.domain.entities.docker_info import DockerInstanceInfo
from dooservice.instance.domain.entities.instance_info import (
    InstanceInfo,
    InstanceStatus,
    ServiceInfo,
    ServiceStatus,
)
from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.instance.infrastructure.driven_adapter.docker_client_adapter import (
    DockerClientAdapter,
)


class FilesystemInstanceAdapter(InstanceRepository):
    """Filesystem-based instance repository implementation."""

    def __init__(self, docker_adapter: DockerClientAdapter):
        self._docker_adapter = docker_adapter

    async def get_instance_info(self, name: str) -> Optional[InstanceInfo]:
        """Get instance information by checking filesystem and Docker."""
        try:
            if not await self.instance_exists(name):
                return None

            docker_info = await self._docker_adapter.get_instance_containers(name)
            services = []

            overall_status = InstanceStatus.STOPPED

            if docker_info.web_container:
                service_status = (
                    ServiceStatus.RUNNING
                    if docker_info.web_container.is_healthy()
                    else ServiceStatus.STOPPED
                )
                services.append(
                    ServiceInfo(
                        name="web",
                        status=service_status,
                        container_id=docker_info.web_container.id,
                    )
                )

            if docker_info.db_container:
                service_status = (
                    ServiceStatus.RUNNING
                    if docker_info.db_container.is_healthy()
                    else ServiceStatus.STOPPED
                )
                services.append(
                    ServiceInfo(
                        name="db",
                        status=service_status,
                        container_id=docker_info.db_container.id,
                    )
                )

            if all(service.status == ServiceStatus.RUNNING for service in services):
                overall_status = InstanceStatus.RUNNING
            elif any(service.status == ServiceStatus.RUNNING for service in services):
                overall_status = InstanceStatus.PARTIAL
            elif services:
                overall_status = InstanceStatus.STOPPED
            else:
                overall_status = InstanceStatus.ERROR

            data_dir = self._get_instance_data_dir(name)

            return InstanceInfo(
                name=name,
                status=overall_status,
                services=services,
                data_dir=data_dir,
                odoo_version="Unknown",
                domain=None,
            )

        except Exception as e:
            raise InstanceOperationException(
                f"Failed to get info for instance '{name}': {str(e)}"
            ) from e

    async def list_instances(self) -> List[InstanceInfo]:
        """List all available instances by checking Docker containers."""
        try:
            instances = []
            containers = self._docker_adapter._get_instance_containers("")

            instance_names = set()
            for container in containers:
                name_parts = container.name.split("_")
                if len(name_parts) >= 2:
                    instance_name = "_".join(name_parts[1:])
                    instance_names.add(instance_name)

            for instance_name in instance_names:
                instance_info = await self.get_instance_info(instance_name)
                if instance_info:
                    instances.append(instance_info)

            return instances

        except Exception as e:
            raise InstanceOperationException(
                f"Failed to list instances: {str(e)}"
            ) from e

    async def instance_exists(self, name: str) -> bool:
        """Check if an instance exists by looking for containers."""
        try:
            docker_info = await self._docker_adapter.get_instance_containers(name)
            return (
                docker_info.web_container is not None
                or docker_info.db_container is not None
            )

        except Exception:  # noqa: BLE001
            return False

    async def get_docker_info(self, name: str) -> Optional[DockerInstanceInfo]:
        """Get Docker container information for an instance."""
        try:
            return await self._docker_adapter.get_instance_containers(name)
        except Exception as e:
            raise InstanceOperationException(
                f"Failed to get Docker info for instance '{name}': {str(e)}"
            ) from e

    async def create_instance_directories(self, name: str, data_dir: str) -> None:
        """Create necessary directories for an instance."""
        try:
            data_path = Path(data_dir)
            data_path.mkdir(parents=True, exist_ok=True)

            subdirs = ["etc", "addons", "logs", "filestore"]
            for subdir in subdirs:
                (data_path / subdir).mkdir(parents=True, exist_ok=True)

        except Exception as e:
            raise InstanceOperationException(
                f"Failed to create directories for instance '{name}': {str(e)}"
            ) from e

    async def delete_instance_directories(
        self, name: str, data_dir: str, force: bool = False
    ) -> None:
        """Delete instance directories."""
        try:
            data_path = Path(data_dir)

            if not data_path.exists():
                return

            if not force:
                if not data_path.is_dir():
                    raise InstanceOperationException(
                        f"Path '{data_dir}' is not a directory"
                    )

                contents = list(data_path.iterdir())
                if contents:
                    raise InstanceOperationException(
                        f"Directory '{data_dir}' is not empty. "
                        f"Use --force to delete anyway."
                    )

            shutil.rmtree(data_path, ignore_errors=True)

        except Exception as e:
            raise InstanceOperationException(
                f"Failed to delete directories for instance '{name}': {str(e)}"
            ) from e

    def _get_instance_data_dir(self, name: str) -> str:
        """Get the data directory for an instance by convention."""
        return f"/opt/odoo-data/{name}"
