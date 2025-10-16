from abc import ABC, abstractmethod
from typing import Dict, Generator, List, Optional, Union

from dooservice.instance.domain.entities.docker_info import (
    ContainerInfo,
    DockerInstanceInfo,
)


class DockerRepository(ABC):
    @abstractmethod
    async def create_containers(self, name: str, config: Dict) -> None:
        """Create Docker containers for an instance."""
        raise NotImplementedError()

    @abstractmethod
    async def start_containers(self, name: str) -> None:
        """Start Docker containers for an instance."""
        raise NotImplementedError()

    @abstractmethod
    async def stop_containers(self, name: str) -> None:
        """Stop Docker containers for an instance."""
        raise NotImplementedError()

    @abstractmethod
    async def delete_containers(self, name: str) -> None:
        """Delete Docker containers for an instance."""
        raise NotImplementedError()

    @abstractmethod
    async def get_container_status(
        self, container_name: str
    ) -> Optional[ContainerInfo]:
        """Get status of a specific container."""
        raise NotImplementedError()

    @abstractmethod
    async def get_instance_containers(self, name: str) -> DockerInstanceInfo:
        """Get all containers for an instance."""
        raise NotImplementedError()

    @abstractmethod
    async def get_container_logs(
        self, container_name: str, lines: int = 100, follow: bool = False
    ) -> Union[str, Generator[str, None, None]]:
        """Get logs from a container.

        Returns string for static logs, generator for streaming.
        """
        raise NotImplementedError()

    @abstractmethod
    async def execute_command(
        self,
        container_name: str,
        command: List[str],
        user: Optional[str] = None,
        workdir: Optional[str] = None,
    ) -> str:
        """Execute a command inside a container."""
        raise NotImplementedError()

    @abstractmethod
    async def create_network(self, name: str) -> None:
        """Create a Docker network for an instance."""
        raise NotImplementedError()

    @abstractmethod
    async def delete_network(self, name: str) -> None:
        """Delete a Docker network for an instance."""
        raise NotImplementedError()
