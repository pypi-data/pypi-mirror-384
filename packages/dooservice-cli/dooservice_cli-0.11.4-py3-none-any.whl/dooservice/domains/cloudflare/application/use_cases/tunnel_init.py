"""Tunnel initialization use case."""

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.domains.cloudflare.domain.entities.tunnel import TunnelConfig
from dooservice.domains.cloudflare.domain.services.tunnel_orchestrator import (
    TunnelOrchestrator,
)


class TunnelInitUseCase:
    """Use case for initializing a new tunnel."""

    def __init__(
        self,
        tunnel_orchestrator: TunnelOrchestrator,
        config: DooServiceConfiguration,
    ):
        self._tunnel_orchestrator = tunnel_orchestrator
        self._config = config

    async def execute(self, tunnel_name: str) -> TunnelConfig:
        """Execute tunnel initialization.

        Args:
            tunnel_name: Name of the tunnel to create

        Returns:
            Created tunnel configuration

        Raises:
            TunnelCreationError: If tunnel creation fails
            ValueError: If tunnel configuration is not found
        """
        # Validate tunnel exists in configuration
        if (
            not self._config.domains.cloudflare
            or not self._config.domains.cloudflare.tunnel
        ):
            raise ValueError(f"Tunnel '{tunnel_name}' not found in configuration")

        tunnel = self._config.domains.cloudflare.tunnel

        # Validate tunnel name matches
        if tunnel.name != tunnel_name:
            raise ValueError(f"Tunnel '{tunnel_name}' not found in configuration")

        account_id = self._config.domains.cloudflare.account_id
        zone_id = self._config.domains.cloudflare.zone_id

        # Initialize tunnel
        return await self._tunnel_orchestrator.initialize_tunnel(
            tunnel_name=tunnel_name,
            account_id=account_id,
            zone_id=zone_id,
            domain=tunnel.domain,
        )
