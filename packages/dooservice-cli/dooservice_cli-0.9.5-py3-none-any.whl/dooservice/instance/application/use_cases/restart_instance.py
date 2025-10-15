"""Restart instance use case."""

from dooservice.instance.application.use_cases.start_instance import StartInstance
from dooservice.instance.application.use_cases.stop_instance import StopInstance
from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.shared.messaging import MessageInterface


class RestartInstance:
    """Use case for restarting an instance."""

    def __init__(
        self,
        stop_instance: StopInstance,
        start_instance: StartInstance,
        messenger: MessageInterface,
    ):
        self._stop_instance = stop_instance
        self._start_instance = start_instance
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
            self._messenger.send_info(f"Restarting instance '{instance_name}'...")

            # Stop the instance
            await self._stop_instance.execute(instance_name)

            # Start the instance
            await self._start_instance.execute(instance_name)

            self._messenger.send_success(
                f"Instance '{instance_name}' restarted successfully"
            )

        except InstanceNotFoundException as e:
            self._messenger.send_error(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.send_error(
                f"Failed to restart instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e
