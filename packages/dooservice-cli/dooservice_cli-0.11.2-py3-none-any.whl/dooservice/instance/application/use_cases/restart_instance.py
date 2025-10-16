"""Restart instance use case."""

from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.docker_repository import DockerRepository
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.shared.messaging import MessageInterface


class RestartInstance:
    """Use case for restarting an instance."""

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
        """Restart an instance by stopping and starting it.

        Args:
            instance_name: Name of the instance to restart

        Raises:
            InstanceNotFoundException: If instance doesn't exist
            InstanceOperationException: If restart operation fails
        """
        try:
            if not await self._instance_repository.instance_exists(instance_name):
                raise InstanceNotFoundException(instance_name)

            with self._messenger.spinner_context(
                f"Restarting instance '{instance_name}'", show_time=True
            ) as spinner:
                docker_info = await self._instance_repository.get_docker_info(
                    instance_name
                )

                if not docker_info:
                    raise InstanceOperationException(
                        f"No Docker containers found for instance '{instance_name}'",
                        instance_name,
                    )

                # Stop containers
                spinner.message = "Stopping containers"
                if docker_info.web_container:
                    await self._docker_repository.stop_containers(
                        docker_info.web_container.name
                    )
                if docker_info.db_container:
                    await self._docker_repository.stop_containers(
                        docker_info.db_container.name
                    )

                # Start containers
                spinner.message = "Starting containers"
                if docker_info.db_container:
                    await self._docker_repository.start_containers(
                        docker_info.db_container.name
                    )
                if docker_info.web_container:
                    await self._docker_repository.start_containers(
                        docker_info.web_container.name
                    )

                spinner.stop(
                    f"Instance '{instance_name}' restarted successfully", success=True
                )

            self._messenger.show_success_animation(
                f"Instance '{instance_name}' is ready!"
            )

        except InstanceNotFoundException as e:
            self._messenger.error_with_icon(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.show_error_animation(
                f"Failed to restart instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e
