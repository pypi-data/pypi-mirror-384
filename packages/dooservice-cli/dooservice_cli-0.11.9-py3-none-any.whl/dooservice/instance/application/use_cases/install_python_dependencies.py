# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""Install Python dependencies use case."""

from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.docker_repository import DockerRepository
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.shared.messaging import MessageInterface


class InstallPythonDependencies:
    """Install Python dependencies in Odoo container."""

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
        instance_config,
        force: bool = False,
        skip_running_check: bool = False,
    ) -> None:
        """
        Install Python dependencies defined in instance configuration.

        Args:
            instance_name: Name of the instance
            instance_config: Instance configuration object
            force: Force reinstall even if already installed
            skip_running_check: Skip container running validation (for create flow)
        """
        try:
            if not await self._instance_repository.instance_exists(instance_name):
                raise InstanceNotFoundException(instance_name)

            # Get python_dependencies from config
            dependencies = (
                instance_config.python_dependencies
                if instance_config.python_dependencies
                else []
            )

            if not dependencies:
                self._messenger.info_with_icon(
                    "No Python dependencies defined in configuration"
                )
                return

            # Get Docker info
            docker_info = await self._instance_repository.get_docker_info(instance_name)

            if not docker_info or not docker_info.web_container:
                raise InstanceOperationException(
                    f"Web container not found for instance '{instance_name}'",
                    instance_name,
                )

            container_name = docker_info.web_container.name

            # Check if container is running (skip if called from create flow)
            if not skip_running_check:
                container_info = await self._docker_repository.get_container_status(
                    container_name
                )
                if not container_info or container_info.status != "running":
                    raise InstanceOperationException(
                        f"Container '{container_name}' is not running. "
                        "Start the instance first.",
                        instance_name,
                    )

            # Determine Odoo version for pip command
            odoo_version = (
                instance_config.odoo_version if instance_config.odoo_version else "19.0"
            )
            odoo_major = int(odoo_version.split(".")[0])

            # For Odoo 18+, use --break-system-packages flag
            use_break_system = odoo_major >= 18

            self._messenger.info_with_icon(
                f"Installing {len(dependencies)} Python package(s) in '{instance_name}'"
            )

            installed = 0
            failed = 0

            for dependency in dependencies:
                try:
                    with self._messenger.spinner_context(
                        f"Installing {dependency}", show_time=True
                    ) as spinner:
                        # Build pip install command
                        cmd = ["pip3", "install"]

                        if use_break_system:
                            cmd.append("--break-system-packages")

                        if force:
                            cmd.append("--force-reinstall")

                        cmd.append(dependency)

                        # Execute as root user
                        await self._docker_repository.execute_command(
                            container_name, cmd, user="root"
                        )

                        spinner.stop(f"Installed {dependency}", success=True)
                        installed += 1

                except Exception as e:  # noqa: BLE001
                    self._messenger.error_with_icon(
                        f"Failed to install {dependency}: {str(e)}"
                    )
                    failed += 1

            # Summary
            if failed == 0:
                self._messenger.success_with_icon(
                    f"Successfully installed all {installed} dependencies"
                )
            elif installed > 0:
                self._messenger.warning_with_icon(
                    f"Installed {installed} dependencies, {failed} failed"
                )
            else:
                raise InstanceOperationException(
                    f"Failed to install all {failed} dependencies", instance_name
                )

        except InstanceNotFoundException as e:
            self._messenger.error_with_icon(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            error_msg = f"Failed to install dependencies in '{instance_name}': {str(e)}"
            self._messenger.show_error_animation(error_msg)
            raise InstanceOperationException(str(e), instance_name) from e
