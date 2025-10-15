from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class InstanceStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    PARTIAL = "partial"
    ERROR = "error"
    UNKNOWN = "unknown"
    NOT_CREATED = "not_created"


class ServiceStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ServiceInfo:
    name: str
    status: ServiceStatus
    container_id: Optional[str] = None
    message: Optional[str] = None


@dataclass
class InstanceInfo:
    name: str
    status: InstanceStatus
    services: List[ServiceInfo]
    data_dir: str
    odoo_version: str
    domain: Optional[str] = None

    def is_healthy(self) -> bool:
        return self.status == InstanceStatus.RUNNING and all(
            service.status == ServiceStatus.RUNNING for service in self.services
        )
