from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.docker_repository import DockerRepository
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.shared.messaging import MessageInterface


class DeleteInstance:
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
        self, instance_name: str, config: DooServiceConfiguration, force: bool = False
    ) -> None:
        """
        Delete an instance completely.

        Args:
            instance_name: Name of the instance to delete
            config: DooService configuration
            force: If True, delete directories even if they contain data.
                   If False, fail if directories are not empty.

        Note: User confirmation should be handled by the CLI layer,
              not in this use case.
        """
        try:
            if not await self._instance_repository.instance_exists(instance_name):
                raise InstanceNotFoundException(instance_name)

            with self._messenger.spinner_context(
                f"Deleting instance '{instance_name}'", show_time=True
            ) as spinner:
                # Stop and remove Docker containers
                spinner.message = "Stopping and removing containers"
                await self._stop_and_remove_containers(instance_name)

                # Remove Docker network
                spinner.message = "Removing Docker network"
                await self._remove_network(instance_name)

                # Remove directories if instance exists in config
                if instance_name in config.instances:
                    spinner.message = "Removing instance directories"
                    instance_config = config.instances[instance_name]
                    await self._remove_directories(
                        instance_name, instance_config.data_dir, force
                    )
                else:
                    self._messenger.warning_with_icon(
                        f"Instance '{instance_name}' not found in configuration, "
                        f"skipping directory cleanup"
                    )

                spinner.stop(
                    f"Instance '{instance_name}' deleted successfully", success=True
                )

            self._messenger.show_success_animation(
                f"Instance '{instance_name}' has been removed"
            )

        except InstanceNotFoundException as e:
            self._messenger.error_with_icon(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.show_error_animation(
                f"Failed to delete instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e

    async def _stop_and_remove_containers(self, instance_name: str) -> None:
        """Stop and remove all containers for the instance."""
        try:
            await self._docker_repository.stop_containers(instance_name)
        except Exception as e:  # noqa: BLE001
            self._messenger.warning_with_icon(f"Failed to stop containers: {str(e)}")

        try:
            await self._docker_repository.delete_containers(instance_name)
        except Exception as e:  # noqa: BLE001
            self._messenger.warning_with_icon(f"Failed to remove containers: {str(e)}")

    async def _remove_network(self, instance_name: str) -> None:
        """Remove Docker network for the instance."""
        try:
            await self._docker_repository.delete_network(f"net_{instance_name}")
        except Exception as e:  # noqa: BLE001
            self._messenger.warning_with_icon(f"Failed to remove network: {str(e)}")

    async def _remove_directories(
        self, instance_name: str, data_dir: str, force: bool
    ) -> None:
        """Remove instance directories."""
        await self._instance_repository.delete_instance_directories(
            instance_name, data_dir, force
        )
