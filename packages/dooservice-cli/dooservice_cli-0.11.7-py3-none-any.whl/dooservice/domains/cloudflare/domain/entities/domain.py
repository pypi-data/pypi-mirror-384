"""Domain entities."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DomainStatus(Enum):
    """Domain status enumeration."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    PENDING = "pending"
    ERROR = "error"


@dataclass
class DomainConfiguration:
    """Domain configuration entity."""

    domain_name: str
    instance_name: str
    tunnel_name: str
    instance_port: int
    status: DomainStatus = DomainStatus.PENDING
    zone_id: Optional[str] = None
    tunnel_id: Optional[str] = None
    dns_record_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class DomainSyncResult:
    """Result of domain synchronization operation."""

    domain_name: str
    success: bool
    message: str
    network_connected: bool = False
    dns_created: bool = False
    tunnel_configured: bool = False
