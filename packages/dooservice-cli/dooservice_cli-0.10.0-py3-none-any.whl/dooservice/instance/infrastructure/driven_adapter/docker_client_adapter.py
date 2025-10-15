from typing import Dict, Generator, List, Optional, Union

import docker
from dooservice.instance.domain.entities.docker_info import (
    ContainerInfo,
    ContainerStatus,
    DockerInstanceInfo,
)
from dooservice.instance.domain.exceptions.instance_exceptions import DockerException
from dooservice.instance.domain.repositories.docker_repository import DockerRepository


class DockerClientAdapter(DockerRepository):
    """Docker implementation using python docker library."""

    def __init__(self):
        try:
            self._client = docker.from_env()
        except Exception as e:  # noqa: BLE001
            raise DockerException(f"Failed to connect to Docker: {str(e)}") from e

    async def create_containers(self, name: str, config: Dict) -> None:
        """Create Docker containers using docker-compose config."""
        try:
            services = config.get("services", {})

            for service_name, service_config in services.items():
                container_name = service_config.get(
                    "container_name", f"{name}_{service_name}"
                )

                if self._container_exists(container_name):
                    continue

                self._create_container(service_config)

        except Exception as e:  # noqa: BLE001
            raise DockerException(
                f"Failed to create containers for '{name}': {str(e)}"
            ) from e

    def _create_container(self, service_config: Dict) -> None:
        """Create a single container from service configuration."""
        container_name = service_config.get("container_name")
        image = service_config.get("image")

        volumes = {}
        if "volumes" in service_config:
            for volume in service_config["volumes"]:
                host_path, container_path = volume.split(":")
                volumes[host_path] = {"bind": container_path, "mode": "rw"}

        ports = {}
        if "ports" in service_config:
            for port in service_config["ports"]:
                host_port, container_port = port.split(":")
                ports[f"{container_port}/tcp"] = host_port

        environment = service_config.get("environment", {})
        networks = service_config.get("networks", [])
        restart_policy = {"Name": service_config.get("restart", "no")}
        user = service_config.get("user")  # Get user from config

        # Build container creation parameters
        create_params = {
            "image": image,
            "name": container_name,
            "environment": environment,
            "volumes": volumes,
            "ports": ports,
            "restart_policy": restart_policy,
            "detach": True,
            "network": networks[0] if networks else None,
        }

        # Add user if specified
        if user:
            create_params["user"] = user

        self._client.containers.create(**create_params)

    async def start_containers(self, name: str) -> None:
        """Start containers for an instance."""
        try:
            containers = self._get_instance_containers(name)

            for container in containers:
                if container.status not in [ContainerStatus.RUNNING]:
                    docker_container = self._client.containers.get(container.id)
                    docker_container.start()

        except Exception as e:  # noqa: BLE001
            raise DockerException(
                f"Failed to start containers for '{name}': {str(e)}"
            ) from e

    async def stop_containers(self, name: str) -> None:
        """Stop containers for an instance."""
        try:
            containers = self._get_instance_containers(name)

            for container in containers:
                if container.status == ContainerStatus.RUNNING:
                    docker_container = self._client.containers.get(container.id)
                    docker_container.stop()

        except Exception as e:  # noqa: BLE001
            raise DockerException(
                f"Failed to stop containers for '{name}': {str(e)}"
            ) from e

    async def delete_containers(self, name: str) -> None:
        """Delete containers for an instance."""
        try:
            containers = self._get_instance_containers(name)

            for container in containers:
                docker_container = self._client.containers.get(container.id)
                if container.status == ContainerStatus.RUNNING:
                    docker_container.stop()
                docker_container.remove()

        except Exception as e:  # noqa: BLE001
            raise DockerException(
                f"Failed to delete containers for '{name}': {str(e)}"
            ) from e

    async def get_container_status(
        self, container_name: str
    ) -> Optional[ContainerInfo]:
        """Get status of a specific container."""
        try:
            container = self._client.containers.get(container_name)
            return self._build_container_info(container)
        except docker.errors.NotFound:
            return None
        except Exception as e:  # noqa: BLE001
            raise DockerException(
                f"Failed to get status for container '{container_name}': {str(e)}"
            ) from e

    async def get_instance_containers(self, name: str) -> DockerInstanceInfo:
        """Get all containers for an instance."""
        containers = self._get_instance_containers(name)

        web_container = None
        db_container = None

        for container in containers:
            if "web" in container.name or "odoo" in container.name:
                web_container = container
            elif "db" in container.name or "postgres" in container.name:
                db_container = container

        return DockerInstanceInfo(
            web_container=web_container, db_container=db_container
        )

    async def get_container_logs(
        self, container_name: str, lines: int = 100, follow: bool = False
    ) -> Union[str, Generator[str, None, None]]:
        """Get logs from a container.

        Returns string for static logs, generator for streaming.
        """
        try:
            container = self._client.containers.get(container_name)

            if follow:
                # Return a generator for streaming logs
                return self._stream_container_logs(container, lines)
            # Return static logs as string
            logs = container.logs(tail=lines)
            return logs.decode("utf-8")

        except docker.errors.NotFound as e:
            raise DockerException(f"Container '{container_name}' not found") from e
        except Exception as e:  # noqa: BLE001
            raise DockerException(
                f"Failed to get logs from container '{container_name}': {str(e)}"
            ) from e

    def _stream_container_logs(
        self, container, lines: int
    ) -> Generator[str, None, None]:
        """Stream logs from a container line by line."""
        try:
            # Get initial logs (tail)
            initial_logs = container.logs(tail=lines)
            if initial_logs:
                for line in initial_logs.decode("utf-8").splitlines():
                    if line.strip():
                        yield line

            # Stream new logs (from now on)
            log_stream = container.logs(follow=True, stream=True, tail=0)
            for log_line in log_stream:
                line = log_line.decode("utf-8").strip()
                if line:
                    yield line
        except Exception as e:  # noqa: BLE001
            yield f"Error streaming logs: {str(e)}"

    async def execute_command(
        self,
        container_name: str,
        command: List[str],
        user: Optional[str] = None,
        workdir: Optional[str] = None,
    ) -> str:
        """Execute a command inside a container."""
        try:
            container = self._client.containers.get(container_name)
            result = container.exec_run(command, user=user, workdir=workdir)

            return result.output.decode("utf-8")

        except docker.errors.NotFound as e:
            raise DockerException(f"Container '{container_name}' not found") from e
        except Exception as e:  # noqa: BLE001
            raise DockerException(
                f"Failed to execute command in container '{container_name}': {str(e)}"
            ) from e

    async def create_network(self, name: str) -> None:
        """Create a Docker network."""
        try:
            if not self._network_exists(name):
                self._client.networks.create(name, driver="bridge")
        except Exception as e:  # noqa: BLE001
            raise DockerException(f"Failed to create network '{name}': {str(e)}") from e

    async def delete_network(self, name: str) -> None:
        """Delete a Docker network."""
        try:
            if self._network_exists(name):
                network = self._client.networks.get(name)
                network.remove()
        except Exception as e:  # noqa: BLE001
            raise DockerException(f"Failed to delete network '{name}': {str(e)}") from e

    def _get_instance_containers(self, name: str) -> List[ContainerInfo]:
        """Get all containers that belong to an instance."""
        try:
            containers = self._client.containers.list(all=True)

            return [
                self._build_container_info(container)
                for container in containers
                if name in container.name
            ]

        except Exception as e:  # noqa: BLE001
            raise DockerException(
                f"Failed to get containers for instance '{name}': {str(e)}"
            ) from e

    def _build_container_info(self, container) -> ContainerInfo:
        """Build ContainerInfo from Docker container object."""
        status_mapping = {
            "running": ContainerStatus.RUNNING,
            "exited": ContainerStatus.EXITED,
            "paused": ContainerStatus.PAUSED,
            "restarting": ContainerStatus.RESTARTING,
            "dead": ContainerStatus.DEAD,
            "created": ContainerStatus.CREATED,
        }

        ports = {}
        if container.ports:
            for container_port, host_bindings in container.ports.items():
                if host_bindings:
                    ports[container_port] = host_bindings[0]["HostPort"]

        return ContainerInfo(
            name=container.name,
            id=container.id,
            status=status_mapping.get(container.status, ContainerStatus.RUNNING),
            image=(
                container.image.tags[0] if container.image.tags else container.image.id
            ),
            ports=ports,
            created_at=container.attrs["Created"],
            started_at=container.attrs.get("State", {}).get("StartedAt"),
            finished_at=container.attrs.get("State", {}).get("FinishedAt"),
            exit_code=container.attrs.get("State", {}).get("ExitCode"),
        )

    def _container_exists(self, container_name: str) -> bool:
        """Check if a container exists."""
        try:
            self._client.containers.get(container_name)
            return True
        except docker.errors.NotFound:
            return False

    def _network_exists(self, network_name: str) -> bool:
        """Check if a network exists."""
        try:
            self._client.networks.get(network_name)
            return True
        except docker.errors.NotFound:
            return False
