from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.docker_repository import DockerRepository
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.instance.domain.services.instance_orchestrator import (
    InstanceOrchestrator,
)
from dooservice.repository.application.use_cases.sync_repositories import (
    SyncRepositoriesUseCase,
)
from dooservice.shared.messaging import MessageInterface


class SyncInstance:
    def __init__(
        self,
        sync_repositories: SyncRepositoriesUseCase,
        instance_repository: InstanceRepository,
        docker_repository: DockerRepository,
        instance_orchestrator: InstanceOrchestrator,
        messenger: MessageInterface,
    ):
        self._sync_repositories = sync_repositories
        self._instance_repository = instance_repository
        self._docker_repository = docker_repository
        self._instance_orchestrator = instance_orchestrator
        self._messenger = messenger

    async def execute(
        self,
        instance_name: str,
        config: DooServiceConfiguration,
        restart_services: bool = True,
    ) -> None:
        """Sync an instance by updating repositories and optionally restarting services.

        Updates repositories and optionally restarts services.
        """
        try:
            if not await self._instance_repository.instance_exists(instance_name):
                raise InstanceNotFoundException(instance_name)

            with self._messenger.spinner_context(
                f"Synchronizing instance '{instance_name}'", show_time=True
            ) as spinner:
                if instance_name not in config.instances:
                    raise InstanceOperationException(
                        f"Instance '{instance_name}' not found in configuration",
                        instance_name,
                    )

                instance_config = config.instances[instance_name]

                await self._sync_repositories_for_instance(
                    instance_name, instance_config, spinner
                )

                spinner.message = "Updating configuration files"
                await self._update_configuration(instance_name, instance_config)

                if restart_services:
                    spinner.message = "Restarting services"
                    await self._restart_services(instance_name)

                spinner.stop(
                    f"Instance '{instance_name}' synchronized successfully",
                    success=True,
                )

            self._messenger.show_success_animation(
                f"Instance '{instance_name}' is in sync!"
            )

        except InstanceNotFoundException as e:
            self._messenger.error_with_icon(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.show_error_animation(
                f"Failed to sync instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e

    async def _sync_repositories_for_instance(
        self, instance_name: str, instance_config, spinner
    ) -> None:
        """Sync all repositories for the instance."""
        if not instance_config.repositories:
            return

        total_repos = len(instance_config.repositories)
        for idx, repo_name in enumerate(instance_config.repositories, 1):
            spinner.message = f"Syncing repository '{repo_name}' ({idx}/{total_repos})"
            try:
                await self._sync_repositories.execute(instance_name, repo_name)
            except Exception as e:  # noqa: BLE001
                self._messenger.warning_with_icon(
                    f"Failed to sync repository '{repo_name}': {str(e)}"
                )

    async def _update_configuration(self, instance_name: str, instance_config) -> None:
        """Update instance configuration files."""
        instance_env = self._instance_orchestrator.prepare_instance_environment(
            instance_name, instance_config
        )

        odoo_config = self._instance_orchestrator.generate_odoo_config(
            instance_env, instance_config
        )

        with open(instance_env.paths.config_file, "w") as f:  # noqa: ASYNC230
            f.write(odoo_config)

        env_file = instance_env.paths.data_dir / ".env"
        with open(env_file, "w") as f:  # noqa: ASYNC230
            for key, value in instance_env.env_vars.items():
                f.write(f"{key}={value}\n")

    async def _restart_services(self, instance_name: str) -> None:
        """Restart services to apply changes."""
        try:
            await self._docker_repository.stop_containers(instance_name)
            await self._docker_repository.start_containers(instance_name)

        except Exception as e:
            self._messenger.warning_with_icon(f"Failed to restart services: {str(e)}")
            raise
