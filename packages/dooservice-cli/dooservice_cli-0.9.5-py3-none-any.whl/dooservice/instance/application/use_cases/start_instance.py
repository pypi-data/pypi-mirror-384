from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.docker_repository import DockerRepository
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.shared.messaging import MessageInterface


class StartInstance:
    def __init__(
        self,
        instance_repository: InstanceRepository,
        docker_repository: DockerRepository,
        messenger: MessageInterface,
    ):
        self._instance_repository = instance_repository
        self._docker_repository = docker_repository
        self._messenger = messenger

    async def execute(self, instance_name: str) -> None:
        """Start an instance by starting its containers in proper order."""
        try:
            if not await self._instance_repository.instance_exists(instance_name):
                raise InstanceNotFoundException(instance_name)

            self._messenger.send_info(f"Starting instance '{instance_name}'...")

            docker_info = await self._instance_repository.get_docker_info(instance_name)

            if not docker_info:
                raise InstanceOperationException(
                    f"No Docker containers found for instance '{instance_name}'",
                    instance_name,
                )

            if docker_info.db_container:
                self._messenger.send_info("Starting database container...")
                await self._start_container(docker_info.db_container.name)

            if docker_info.web_container:
                self._messenger.send_info("Starting web container...")
                await self._start_container(docker_info.web_container.name)

            self._messenger.send_success(
                f"Instance '{instance_name}' started successfully"
            )

        except InstanceNotFoundException as e:
            self._messenger.send_error(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.send_error(
                f"Failed to start instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e

    async def _start_container(self, container_name: str) -> None:
        """Start a specific container and verify it's running."""
        try:
            await self._docker_repository.start_containers(container_name)

            container_info = await self._docker_repository.get_container_status(
                container_name
            )
            if container_info and container_info.is_healthy():
                self._messenger.send_success(
                    f"Container '{container_name}' started successfully"
                )
            else:
                self._messenger.send_warning(
                    f"Container '{container_name}' started but may not be healthy"
                )

        except Exception as e:
            self._messenger.send_error(
                f"Failed to start container '{container_name}': {str(e)}"
            )
            raise
