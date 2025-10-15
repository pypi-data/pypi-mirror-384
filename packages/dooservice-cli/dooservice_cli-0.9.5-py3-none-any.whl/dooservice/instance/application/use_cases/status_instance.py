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
            self._messenger.send_error(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.send_error(
                f"Failed to get status for instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e

    def _display_status(self, instance_info: InstanceInfo) -> None:
        """Display instance status information."""
        self._messenger.send_info(f"Instance: {instance_info.name}")
        self._messenger.send_info(f"Status: {instance_info.status.value}")
        self._messenger.send_info(f"Odoo Version: {instance_info.odoo_version}")
        self._messenger.send_info(f"Data Directory: {instance_info.data_dir}")

        if instance_info.domain:
            self._messenger.send_info(f"Domain: {instance_info.domain}")

        self._messenger.send_info("Services:")
        for service in instance_info.services:
            # status_color = "success" if service.status.value == "running" else "error"  # noqa: F841,E501
            self._messenger.send_info(f"  - {service.name}: {service.status.value}")

            if service.container_id:
                self._messenger.send_info(f"    Container ID: {service.container_id}")

            if service.message:
                self._messenger.send_info(f"    Message: {service.message}")

        if instance_info.is_healthy():
            self._messenger.send_success("Instance is healthy and running")
        else:
            self._messenger.send_warning("Instance has issues or is not fully running")
