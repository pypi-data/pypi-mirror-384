"""Tunnel domain entities."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TunnelConfig:
    """Tunnel configuration entity."""

    tunnel_id: str
    name: str
    account_id: str
    created_at: str
    deleted_at: Optional[str] = None
    connections: List[Dict] = None

    def __post_init__(self):
        if self.connections is None:
            self.connections = []


@dataclass
class TunnelIngress:
    """Tunnel ingress rule entity."""

    hostname: str
    service: str
    path: Optional[str] = None
    origin_request: Optional[Dict] = None


@dataclass
class TunnelConfiguration:
    """Complete tunnel configuration entity."""

    tunnel_id: str
    ingress: List[TunnelIngress]
    warp_routing: Optional[Dict] = None
    origin_request: Optional[Dict] = None

    def __post_init__(self):
        if self.ingress is None:
            self.ingress = []


@dataclass
class TunnelDNSRecord:
    """DNS record entity for tunnel."""

    record_id: Optional[str]
    zone_id: str
    name: str
    type: str
    content: str
    ttl: int = 300
    proxied: bool = True
