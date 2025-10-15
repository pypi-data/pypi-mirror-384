from typing import List, Optional

from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.docker_repository import DockerRepository
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.shared.messaging import MessageInterface


class ExecInstance:
    def __init__(
        self,
        instance_repository: InstanceRepository,
        docker_repository: DockerRepository,
        messenger: MessageInterface,
    ):
        self._instance_repository = instance_repository
        self._docker_repository = docker_repository
        self._messenger = messenger

    async def execute(
        self,
        instance_name: str,
        command: List[str],
        service: Optional[str] = "web",
        user: Optional[str] = None,
        workdir: Optional[str] = None,
    ) -> str:
        """Execute a command inside an instance container."""
        try:
            if not await self._instance_repository.instance_exists(instance_name):
                raise InstanceNotFoundException(instance_name)

            docker_info = await self._instance_repository.get_docker_info(instance_name)

            if not docker_info:
                raise InstanceOperationException(
                    f"No Docker containers found for instance '{instance_name}'",
                    instance_name,
                )

            container_name = self._get_container_name(docker_info, service)

            self._messenger.info_with_icon(
                f"Executing command in {service} service: {' '.join(command)}"
            )

            return await self._docker_repository.execute_command(
                container_name, command, user=user, workdir=workdir
            )

        except InstanceNotFoundException as e:
            self._messenger.error_with_icon(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.show_error_animation(
                f"Failed to execute command in instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e

    def _get_container_name(self, docker_info, service: str) -> str:
        """Get container name for the specified service."""
        if service == "web" and docker_info.web_container:
            return docker_info.web_container.name
        if service == "db" and docker_info.db_container:
            return docker_info.db_container.name
        available_services = []
        if docker_info.web_container:
            available_services.append("web")
        if docker_info.db_container:
            available_services.append("db")

        raise InstanceOperationException(
            f"Service '{service}' not found. Available services: {', '.join(available_services)}"  # noqa: E501
        )
