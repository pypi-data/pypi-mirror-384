"""Tunnel repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from dooservice.domains.cloudflare.domain.entities.tunnel import (
    TunnelConfig,
    TunnelConfiguration,
)


class TunnelRepository(ABC):
    """Abstract repository for tunnel operations."""

    @abstractmethod
    async def create_tunnel(self, name: str, account_id: str) -> TunnelConfig:
        """Create a new tunnel.

        Args:
            name: Tunnel name
            account_id: Cloudflare account ID

        Returns:
            Created tunnel configuration
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_tunnel(
        self, tunnel_id: str, account_id: str
    ) -> Optional[TunnelConfig]:
        """Get tunnel by ID.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID

        Returns:
            Tunnel configuration if found, None otherwise
        """
        raise NotImplementedError()

    @abstractmethod
    async def list_tunnels(self, account_id: str) -> List[TunnelConfig]:
        """List all tunnels for account.

        Args:
            account_id: Cloudflare account ID

        Returns:
            List of tunnel configurations
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete_tunnel(self, tunnel_id: str, account_id: str) -> bool:
        """Delete tunnel.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID

        Returns:
            True if deleted successfully
        """
        raise NotImplementedError()

    @abstractmethod
    async def configure_tunnel(
        self, tunnel_id: str, account_id: str, configuration: TunnelConfiguration
    ) -> bool:
        """Configure tunnel ingress rules.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID
            configuration: Tunnel configuration

        Returns:
            True if configured successfully
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_tunnel_token(self, tunnel_id: str, account_id: str) -> str:
        """Get tunnel token for running cloudflared.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID

        Returns:
            Tunnel token
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_tunnel_configuration(
        self, tunnel_id: str, account_id: str
    ) -> Optional[TunnelConfiguration]:
        """Get tunnel configuration.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID

        Returns:
            Tunnel configuration if found, None otherwise
        """
        raise NotImplementedError()

    @abstractmethod
    async def remove_domain_from_tunnel(
        self, tunnel_id: str, account_id: str, domain_name: str
    ) -> bool:
        """Remove a specific domain from tunnel configuration.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID
            domain_name: Domain name to remove

        Returns:
            True if removed successfully
        """
        raise NotImplementedError()
