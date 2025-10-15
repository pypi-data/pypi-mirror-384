from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.docker_repository import DockerRepository
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.shared.messaging import MessageInterface


class StopInstance:
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
        """Stop an instance by stopping its containers in proper order."""
        try:
            if not await self._instance_repository.instance_exists(instance_name):
                raise InstanceNotFoundException(instance_name)

            self._messenger.send_info(f"Stopping instance '{instance_name}'...")

            docker_info = await self._instance_repository.get_docker_info(instance_name)

            if not docker_info:
                raise InstanceOperationException(
                    f"No Docker containers found for instance '{instance_name}'",
                    instance_name,
                )

            if docker_info.web_container:
                self._messenger.send_info("Stopping web container...")
                await self._stop_container(docker_info.web_container.name)

            if docker_info.db_container:
                self._messenger.send_info("Stopping database container...")
                await self._stop_container(docker_info.db_container.name)

            self._messenger.send_success(
                f"Instance '{instance_name}' stopped successfully"
            )

        except InstanceNotFoundException as e:
            self._messenger.send_error(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.send_error(
                f"Failed to stop instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e

    async def _stop_container(self, container_name: str) -> None:
        """Stop a specific container."""
        try:
            await self._docker_repository.stop_containers(container_name)
            self._messenger.send_success(
                f"Container '{container_name}' stopped successfully"
            )

        except Exception as e:
            self._messenger.send_error(
                f"Failed to stop container '{container_name}': {str(e)}"
            )
            raise
