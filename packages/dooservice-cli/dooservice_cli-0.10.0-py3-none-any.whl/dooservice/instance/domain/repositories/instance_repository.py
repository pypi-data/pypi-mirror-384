from abc import ABC, abstractmethod
from typing import List, Optional

from dooservice.instance.domain.entities.docker_info import DockerInstanceInfo
from dooservice.instance.domain.entities.instance_info import InstanceInfo


class InstanceRepository(ABC):
    @abstractmethod
    async def get_instance_info(self, name: str) -> Optional[InstanceInfo]:
        """Get instance information by name."""
        raise NotImplementedError()

    @abstractmethod
    async def list_instances(self) -> List[InstanceInfo]:
        """List all available instances."""
        raise NotImplementedError()

    @abstractmethod
    async def instance_exists(self, name: str) -> bool:
        """Check if an instance exists."""
        raise NotImplementedError()

    @abstractmethod
    async def get_docker_info(self, name: str) -> Optional[DockerInstanceInfo]:
        """Get Docker container information for an instance."""
        raise NotImplementedError()

    @abstractmethod
    async def create_instance_directories(self, name: str, data_dir: str) -> None:
        """Create necessary directories for an instance."""
        raise NotImplementedError()

    @abstractmethod
    async def delete_instance_directories(
        self, name: str, data_dir: str, force: bool = False
    ) -> None:
        """Delete instance directories."""
        raise NotImplementedError()
