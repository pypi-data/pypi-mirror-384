"""DNS repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from dooservice.domains.cloudflare.domain.entities.tunnel import TunnelDNSRecord


class DNSRepository(ABC):
    """Abstract repository for DNS operations."""

    @abstractmethod
    async def create_dns_record(self, record: TunnelDNSRecord) -> TunnelDNSRecord:
        """Create a DNS record.

        Args:
            record: DNS record to create

        Returns:
            Created DNS record with record_id
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_dns_record(
        self, zone_id: str, record_name: str
    ) -> Optional[TunnelDNSRecord]:
        """Get DNS record by name.

        Args:
            zone_id: Cloudflare zone ID
            record_name: DNS record name

        Returns:
            DNS record if found, None otherwise
        """
        raise NotImplementedError()

    @abstractmethod
    async def update_dns_record(self, record: TunnelDNSRecord) -> bool:
        """Update DNS record.

        Args:
            record: DNS record to update

        Returns:
            True if updated successfully
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete_dns_record(self, zone_id: str, record_id: str) -> bool:
        """Delete DNS record.

        Args:
            zone_id: Cloudflare zone ID
            record_id: DNS record ID

        Returns:
            True if deleted successfully
        """
        raise NotImplementedError()

    @abstractmethod
    async def list_dns_records(self, zone_id: str) -> List[TunnelDNSRecord]:
        """List all DNS records in zone.

        Args:
            zone_id: Cloudflare zone ID

        Returns:
            List of DNS records
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_tunnel_dns_records(
        self, zone_id: str, tunnel_id: str
    ) -> List[TunnelDNSRecord]:
        """Get DNS records pointing to a specific tunnel.

        Args:
            zone_id: Cloudflare zone ID
            tunnel_id: Tunnel ID

        Returns:
            List of DNS records pointing to the tunnel
        """
        raise NotImplementedError()
