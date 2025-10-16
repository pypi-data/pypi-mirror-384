from dooservice.instance.domain.entities.instance_info import InstanceInfo
from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.shared.messaging import MessageInterface


class StatusInstance:
    def __init__(
        self, instance_repository: InstanceRepository, messenger: MessageInterface
    ):
        self._instance_repository = instance_repository
        self._messenger = messenger

    async def execute(self, instance_name: str) -> InstanceInfo:
        """Get the status of an instance."""
        try:
            if not await self._instance_repository.instance_exists(instance_name):
                raise InstanceNotFoundException(instance_name)

            instance_info = await self._instance_repository.get_instance_info(
                instance_name
            )

            if not instance_info:
                raise InstanceOperationException(
                    f"Could not retrieve status for instance '{instance_name}'",
                    instance_name,
                )

            self._display_status(instance_info)

            return instance_info

        except InstanceNotFoundException as e:
            self._messenger.error_with_icon(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.show_error_animation(
                f"Failed to get status for instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e

    def _display_status(self, instance_info: InstanceInfo) -> None:
        """Display instance status information."""
        # Use the messenger's show_instance_status for a richer display
        details = {
            "Odoo Version": instance_info.odoo_version,
            "Data Directory": instance_info.data_dir,
        }

        if instance_info.domain:
            details["Domain"] = instance_info.domain

        self._messenger.show_instance_status(
            instance_info.name, instance_info.status.value, details
        )

        if instance_info.is_healthy():
            self._messenger.success_with_icon("Instance is healthy and running")
        else:
            self._messenger.warning_with_icon(
                "Instance has issues or is not fully running"
            )
