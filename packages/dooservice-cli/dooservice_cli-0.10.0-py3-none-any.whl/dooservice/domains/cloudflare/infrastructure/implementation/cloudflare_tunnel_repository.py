"""Cloudflare tunnel repository implementation."""

from typing import List, Optional

from dooservice.domains.cloudflare.domain.entities.tunnel import (
    TunnelConfig,
    TunnelConfiguration,
    TunnelIngress,
)
from dooservice.domains.cloudflare.domain.repositories.tunnel_repository import (
    TunnelRepository,
)
from dooservice.domains.cloudflare.infrastructure.driven_adapter.cloudflare_api.cloudflare_client import (  # noqa: E501
    CloudflareAPIClient,
)


class CloudflareTunnelRepository(TunnelRepository):
    """Cloudflare tunnel repository implementation."""

    def __init__(self, api_client: CloudflareAPIClient):
        self._api_client = api_client

    async def create_tunnel(self, name: str, account_id: str) -> TunnelConfig:
        """Create a new tunnel."""
        tunnel_data = await self._api_client.create_tunnel(name, account_id)

        return TunnelConfig(
            tunnel_id=tunnel_data["id"],
            name=tunnel_data["name"],
            account_id=account_id,
            created_at=tunnel_data.get("created_at", ""),
            deleted_at=tunnel_data.get("deleted_at"),
            connections=tunnel_data.get("connections", []),
        )

    async def get_tunnel(
        self, tunnel_id: str, account_id: str
    ) -> Optional[TunnelConfig]:
        """Get tunnel by ID."""
        tunnel_data = await self._api_client.get_tunnel(tunnel_id, account_id)

        if not tunnel_data:
            return None

        return TunnelConfig(
            tunnel_id=tunnel_data["id"],
            name=tunnel_data["name"],
            account_id=account_id,
            created_at=tunnel_data.get("created_at", ""),
            deleted_at=tunnel_data.get("deleted_at"),
            connections=tunnel_data.get("connections", []),
        )

    async def list_tunnels(self, account_id: str) -> List[TunnelConfig]:
        """List all active (non-deleted) tunnels for account."""
        tunnels_data = await self._api_client.list_tunnels(account_id)

        tunnels = []
        for tunnel_data in tunnels_data:
            # Skip deleted tunnels
            if tunnel_data.get("deleted_at"):
                continue

            tunnels.append(
                TunnelConfig(
                    tunnel_id=tunnel_data["id"],
                    name=tunnel_data["name"],
                    account_id=account_id,
                    created_at=tunnel_data.get("created_at", ""),
                    deleted_at=tunnel_data.get("deleted_at"),
                    connections=tunnel_data.get("connections", []),
                )
            )

        return tunnels

    async def delete_tunnel(self, tunnel_id: str, account_id: str) -> bool:
        """Delete tunnel."""
        return await self._api_client.delete_tunnel(tunnel_id, account_id)

    async def configure_tunnel(
        self, tunnel_id: str, account_id: str, configuration: TunnelConfiguration
    ) -> bool:
        """Configure tunnel ingress rules."""
        # Convert domain entities to API format
        ingress_rules = []
        for ingress in configuration.ingress:
            rule = {
                "hostname": ingress.hostname,
                "service": ingress.service,
            }
            if ingress.path:
                rule["path"] = ingress.path
            if ingress.origin_request:
                rule["originRequest"] = ingress.origin_request

            ingress_rules.append(rule)

        # Add catch-all rule (required by Cloudflare)
        ingress_rules.append({"service": "http_status:404"})

        config_data = {
            "config": {
                "ingress": ingress_rules,
            }
        }

        if configuration.warp_routing:
            config_data["config"]["warp-routing"] = configuration.warp_routing

        if configuration.origin_request:
            config_data["config"]["originRequest"] = configuration.origin_request

        return await self._api_client.configure_tunnel(
            tunnel_id, account_id, config_data
        )

    async def get_tunnel_token(self, tunnel_id: str, account_id: str) -> str:
        """Get tunnel token for running cloudflared."""
        return await self._api_client.get_tunnel_token(tunnel_id, account_id)

    async def get_tunnel_configuration(
        self, tunnel_id: str, account_id: str
    ) -> Optional[TunnelConfiguration]:
        """Get tunnel configuration."""
        config_data = await self._api_client.get_tunnel_configuration(
            tunnel_id, account_id
        )

        if not config_data or not config_data.get("config"):
            return None

        ingress_rules = []
        config = config_data["config"]

        if "ingress" in config:
            for rule in config["ingress"]:
                # Skip catch-all rule
                if rule.get("service") == "http_status:404":
                    continue

                ingress_rules.append(
                    TunnelIngress(
                        hostname=rule.get("hostname"),
                        service=rule.get("service"),
                        path=rule.get("path"),
                        origin_request=rule.get("originRequest"),
                    )
                )

        return TunnelConfiguration(
            tunnel_id=tunnel_id,
            ingress=ingress_rules,
            warp_routing=config.get("warp-routing"),
            origin_request=config.get("originRequest"),
        )

    async def remove_domain_from_tunnel(
        self, tunnel_id: str, account_id: str, domain_name: str
    ) -> bool:
        """Remove a specific domain from tunnel configuration."""
        try:
            # Get current configuration
            current_config = await self.get_tunnel_configuration(tunnel_id, account_id)

            if not current_config or not current_config.ingress:
                return True  # Nothing to remove

            # Filter out the domain
            updated_ingress = [
                ingress
                for ingress in current_config.ingress
                if ingress.hostname != domain_name
            ]

            # Create new configuration
            new_config = TunnelConfiguration(
                tunnel_id=tunnel_id,
                ingress=updated_ingress,
                warp_routing=current_config.warp_routing,
                origin_request=current_config.origin_request,
            )

            # Update configuration
            return await self.configure_tunnel(tunnel_id, account_id, new_config)

        except Exception:  # noqa: BLE001
            return False
