"""Use case for updating Odoo modules in an instance."""

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


class UpdateOdooModules:
    """Use case to update Odoo modules using odoo-bin command."""

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
        database: str,
        modules: Optional[List[str]] = None,
        update_all: bool = False,
        http_port: int = 9090,
    ) -> str:
        """
        Update Odoo modules in the specified instance.

        Args:
            instance_name: Name of the instance
            database: Name of the Odoo database
            modules: List of module names to update (e.g., ['sale', 'purchase'])
            update_all: If True, update all modules (equivalent to -u all)
            http_port: HTTP port to use (default 9090 to avoid conflicts)

        Returns:
            Command output as string
        """
        try:
            # Verify instance exists
            if not await self._instance_repository.instance_exists(instance_name):
                raise InstanceNotFoundException(instance_name)

            # Get Docker info to find the web container
            docker_info = await self._instance_repository.get_docker_info(instance_name)

            if not docker_info or not docker_info.web_container:
                raise InstanceOperationException(
                    f"No web container found for instance '{instance_name}'",
                    instance_name,
                )

            container_name = docker_info.web_container.name

            # Build the Odoo command
            modules_str = self._build_modules_string(modules, update_all)

            with self._messenger.spinner_context(
                f"Updating modules {modules_str} in database '{database}'",
                show_time=True,
            ) as spinner:
                command = self._build_odoo_command(database, modules_str, http_port)

                spinner.message = "Executing update command"

                # Execute the command in the container
                result = await self._docker_repository.execute_command(
                    container_name=container_name,
                    command=command,
                    user=None,  # Use default container user
                    workdir=None,  # Use default working directory
                )

                spinner.stop(
                    f"Modules update completed for database '{database}'", success=True
                )

            self._messenger.success_with_icon(
                f"Database '{database}' modules updated successfully"
            )

            return result

        except InstanceNotFoundException as e:
            self._messenger.error_with_icon(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.show_error_animation(
                f"Failed to update modules in instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e

    def _build_modules_string(
        self, modules: Optional[List[str]], update_all: bool
    ) -> str:
        """Build the modules string for the command."""
        if update_all:
            return "all"
        if modules:
            return ",".join(modules)
        raise ValueError("Either modules list or update_all must be specified")

    def _build_odoo_command(
        self, database: str, modules_str: str, http_port: int
    ) -> List[str]:
        """
        Build the Odoo command to update modules.

        Command structure:
        odoo -c /etc/odoo/odoo.conf -d <database> -u <modules>
             --stop-after-init --http-port <port>
        """
        return [
            "odoo",
            "-c",
            "/etc/odoo/odoo.conf",
            "-d",
            database,
            "-u",
            modules_str,
            "--stop-after-init",
            "--http-port",
            str(http_port),
        ]
