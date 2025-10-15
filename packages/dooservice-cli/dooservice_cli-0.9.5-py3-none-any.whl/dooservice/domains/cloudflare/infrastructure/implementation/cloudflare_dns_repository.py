"""Cloudflare DNS repository implementation."""

from typing import List, Optional

from dooservice.domains.cloudflare.domain.entities.tunnel import TunnelDNSRecord
from dooservice.domains.cloudflare.domain.repositories.dns_repository import (
    DNSRepository,
)
from dooservice.domains.cloudflare.infrastructure.driven_adapter.cloudflare_api.cloudflare_client import (  # noqa: E501
    CloudflareAPIClient,
)


class CloudflareDNSRepository(DNSRepository):
    """Cloudflare DNS repository implementation."""

    def __init__(self, api_client: CloudflareAPIClient):
        self._api_client = api_client

    async def create_dns_record(self, record: TunnelDNSRecord) -> TunnelDNSRecord:
        """Create a DNS record."""
        record_data = {
            "type": record.type,
            "name": record.name,
            "content": record.content,
            "ttl": record.ttl,
            "proxied": record.proxied,
        }

        created_record = await self._api_client.create_dns_record(
            record.zone_id, record_data
        )

        return TunnelDNSRecord(
            record_id=created_record["id"],
            zone_id=record.zone_id,
            name=created_record["name"],
            type=created_record["type"],
            content=created_record["content"],
            ttl=created_record["ttl"],
            proxied=created_record.get("proxied", True),
        )

    async def get_dns_record(
        self, zone_id: str, record_name: str
    ) -> Optional[TunnelDNSRecord]:
        """Get DNS record by name."""
        record_data = await self._api_client.get_dns_record(zone_id, record_name)

        if not record_data:
            return None

        return TunnelDNSRecord(
            record_id=record_data["id"],
            zone_id=zone_id,
            name=record_data["name"],
            type=record_data["type"],
            content=record_data["content"],
            ttl=record_data["ttl"],
            proxied=record_data.get("proxied", True),
        )

    async def update_dns_record(self, record: TunnelDNSRecord) -> bool:
        """Update DNS record."""
        # Note: This would require implementing update functionality in
        # CloudflareAPIClient
        # For now, we'll return False to indicate it's not implemented
        return False

    async def delete_dns_record(self, zone_id: str, record_id: str) -> bool:
        """Delete DNS record."""
        return await self._api_client.delete_dns_record(zone_id, record_id)

    async def list_dns_records(self, zone_id: str) -> List[TunnelDNSRecord]:
        """List all DNS records in zone."""
        # Note: This would require implementing list functionality in
        # CloudflareAPIClient
        # For now, we'll return an empty list
        return []

    async def get_tunnel_dns_records(
        self, zone_id: str, tunnel_id: str
    ) -> List[TunnelDNSRecord]:
        """Get DNS records pointing to a specific tunnel."""
        records_data = await self._api_client.list_dns_records(zone_id, tunnel_id)

        return [
            TunnelDNSRecord(
                record_id=record_data["id"],
                zone_id=zone_id,
                name=record_data["name"],
                type=record_data["type"],
                content=record_data["content"],
                ttl=record_data["ttl"],
                proxied=record_data.get("proxied", True),
            )
            for record_data in records_data
        ]
