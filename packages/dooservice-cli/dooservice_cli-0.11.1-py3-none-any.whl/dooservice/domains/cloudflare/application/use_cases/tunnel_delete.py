"""Tunnel delete use case."""

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.domains.cloudflare.domain.exceptions.tunnel_exceptions import (
    TunnelNotFoundError,
)
from dooservice.domains.cloudflare.domain.services.tunnel_orchestrator import (
    TunnelOrchestrator,
)


class TunnelDeleteUseCase:
    """Use case for deleting tunnels."""

    def __init__(
        self,
        tunnel_orchestrator: TunnelOrchestrator,
        config: DooServiceConfiguration,
    ):
        self._tunnel_orchestrator = tunnel_orchestrator
        self._config = config

    async def execute(self, tunnel_name: str, force: bool = False) -> bool:
        """Execute tunnel deletion.

        Args:
            tunnel_name: Name of the tunnel to delete
            force: Force delete without confirmation

        Returns:
            True if deleted successfully

        Raises:
            TunnelNotFoundError: If tunnel is not found
        """
        if not self._config.domains.cloudflare:
            raise TunnelNotFoundError("Cloudflare configuration not found")

        account_id = self._config.domains.cloudflare.account_id

        # Get all tunnels with this name
        tunnels = await self._tunnel_orchestrator._tunnel_repository.list_tunnels(
            account_id
        )
        tunnels_to_delete = [t for t in tunnels if t.name == tunnel_name]

        if not tunnels_to_delete:
            raise TunnelNotFoundError(f"No tunnels found with name '{tunnel_name}'")

        success_count = 0
        for tunnel in tunnels_to_delete:
            try:
                success = await self._tunnel_orchestrator.delete_tunnel_complete(
                    tunnel.tunnel_id, account_id, tunnel_name
                )
                if success:
                    success_count += 1
            except (ValueError, RuntimeError, ConnectionError):
                continue

        return success_count > 0
