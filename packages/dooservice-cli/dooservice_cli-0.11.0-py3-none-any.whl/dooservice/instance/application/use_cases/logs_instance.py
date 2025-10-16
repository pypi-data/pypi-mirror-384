from typing import Generator, Optional, Union

from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.docker_repository import DockerRepository
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.shared.messaging import MessageInterface


class LogsInstance:
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
        service: Optional[str] = None,
        tail: int = 100,
        follow: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """Get logs from an instance."""
        try:
            if not await self._instance_repository.instance_exists(instance_name):
                raise InstanceNotFoundException(instance_name)

            docker_info = await self._instance_repository.get_docker_info(instance_name)

            if not docker_info:
                raise InstanceOperationException(
                    f"No Docker containers found for instance '{instance_name}'",
                    instance_name,
                )

            if service:
                return await self._get_service_logs(docker_info, service, tail, follow)
            return await self._get_all_logs(docker_info, tail, follow)

        except InstanceNotFoundException as e:
            self._messenger.error_with_icon(str(e))
            raise
        except Exception as e:  # noqa: BLE001
            self._messenger.show_error_animation(
                f"Failed to get logs for instance '{instance_name}': {str(e)}"
            )
            raise InstanceOperationException(str(e), instance_name) from e

    async def _get_service_logs(
        self, docker_info, service: str, tail: int, follow: bool
    ) -> Union[str, Generator[str, None, None]]:
        """Get logs from a specific service."""
        container_name = None

        if service == "web" and docker_info.web_container:
            container_name = docker_info.web_container.name
        elif service == "db" and docker_info.db_container:
            container_name = docker_info.db_container.name
        else:
            available_services = []
            if docker_info.web_container:
                available_services.append("web")
            if docker_info.db_container:
                available_services.append("db")

            raise InstanceOperationException(
                f"Service '{service}' not found. Available services: {', '.join(available_services)}"  # noqa: E501
            )

        self._messenger.info_with_icon(f"Getting logs from {service} service...")
        logs = await self._docker_repository.get_container_logs(
            container_name, tail, follow
        )

        if follow:
            self._messenger.info_with_icon(
                f"Following logs from {service} service (Press Ctrl+C to exit)..."
            )

        return logs

    async def _get_all_logs(
        self, docker_info, tail: int, follow: bool
    ) -> Union[str, Generator[str, None, None]]:
        """Get logs from all services."""
        # Following logs from multiple services is complex, require service
        # specification
        if follow:
            available_services = []
            if docker_info.web_container:
                available_services.append("web")
            if docker_info.db_container:
                available_services.append("db")

            raise InstanceOperationException(
                f"When using --follow, please specify a service. Available services: {', '.join(available_services)}"  # noqa: E501
            )

        all_logs = []

        if docker_info.web_container:
            self._messenger.info_with_icon("Getting logs from web service...")
            web_logs = await self._docker_repository.get_container_logs(
                docker_info.web_container.name, tail, follow
            )
            all_logs.append(f"=== WEB SERVICE LOGS ===\n{web_logs}")

        if docker_info.db_container:
            self._messenger.info_with_icon("Getting logs from database service...")
            db_logs = await self._docker_repository.get_container_logs(
                docker_info.db_container.name, tail, follow
            )
            all_logs.append(f"=== DATABASE SERVICE LOGS ===\n{db_logs}")

        return "\n\n".join(all_logs)
