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

            with self._messenger.spinner_context(
                f"Stopping instance '{instance_name}'", show_time=True
            ) as spinner:
                docker_info = await self._instance_repository.get_docker_info(
                    instance_name
                )

                if not docker_info:
                    raise InstanceOperationException(
                        f"No Docker containers found for instance '{instance_name}'",
                        instance_name,
                    )

                if docker_info.web_container:
                    spinner.message = "Stopping web container"
                    await self._stop_container(docker_info.web_container.name)

                if docker_info.db_container:
                    spinner.message = "Stopping database container"
                    await self._stop_container(docker_info.db_container.name)

                spinner.stop(
                    f"Instance '{instance_name}' stopped successfully", success=True
                )

            self._messenger.success_with_icon(
                f"Instance '{instance_name}' has been stopped"
            )

        except InstanceNotFoundException as e:
            self._messenger.error_with_icon(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.show_error_animation(
                f"Failed to stop instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e

    async def _stop_container(self, container_name: str) -> None:
        """Stop a specific container."""
        try:
            await self._docker_repository.stop_containers(container_name)

        except Exception as e:
            self._messenger.error_with_icon(
                f"Failed to stop container '{container_name}': {str(e)}"
            )
            raise
