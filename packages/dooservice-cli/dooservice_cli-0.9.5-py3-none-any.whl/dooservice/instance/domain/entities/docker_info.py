from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ContainerStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    RESTARTING = "restarting"
    DEAD = "dead"
    CREATED = "created"
    EXITED = "exited"


@dataclass
class ContainerInfo:
    name: str
    id: str
    status: ContainerStatus
    image: str
    ports: Dict[str, str]
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None

    def is_healthy(self) -> bool:
        return self.status == ContainerStatus.RUNNING


@dataclass
class NetworkInfo:
    name: str
    id: str
    driver: str
    containers: List[str]


@dataclass
class VolumeInfo:
    name: str
    mount_point: str
    driver: str
    size: Optional[int] = None


@dataclass
class DockerInstanceInfo:
    web_container: Optional[ContainerInfo] = None
    db_container: Optional[ContainerInfo] = None
    network: Optional[NetworkInfo] = None
    volumes: List[VolumeInfo] = None

    def get_containers(self) -> List[ContainerInfo]:
        containers = []
        if self.web_container:
            containers.append(self.web_container)
        if self.db_container:
            containers.append(self.db_container)
        return containers

    def is_running(self) -> bool:
        containers = self.get_containers()
        if not containers:
            return False
        return all(container.is_healthy() for container in containers)

    def is_partially_running(self) -> bool:
        containers = self.get_containers()
        if not containers:
            return False
        return any(container.is_healthy() for container in containers)
