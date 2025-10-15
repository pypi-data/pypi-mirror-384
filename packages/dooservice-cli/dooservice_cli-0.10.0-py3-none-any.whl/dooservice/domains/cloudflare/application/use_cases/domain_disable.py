"""Domain disable use case."""

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.domains.cloudflare.domain.exceptions.domain_exceptions import (
    DomainNotFoundError,
)
from dooservice.domains.cloudflare.domain.services.tunnel_orchestrator import (
    TunnelOrchestrator,
)


class DomainDisableUseCase:
    """Use case for disabling a domain."""

    def __init__(
        self,
        tunnel_orchestrator: TunnelOrchestrator,
        config: DooServiceConfiguration,
    ):
        self._tunnel_orchestrator = tunnel_orchestrator
        self._config = config

    async def execute(self, domain_name: str) -> bool:
        """Execute domain disabling.

        Args:
            domain_name: Domain name to disable

        Returns:
            True if domain was disabled successfully

        Raises:
            DomainNotFoundError: If domain is not found in configuration
        """
        # Find domain in configuration
        if domain_name not in self._config.domains.base_domains:
            raise DomainNotFoundError(
                f"Domain '{domain_name}' not found in configuration"
            )

        base_domain = self._config.domains.base_domains[domain_name]
        instance_name = base_domain.instance

        # Find tunnel for domain
        tunnel_name = None
        zone_id = None

        if self._config.domains.cloudflare and self._config.domains.cloudflare.tunnel:
            tunnel = self._config.domains.cloudflare.tunnel
            if base_domain.name.endswith(tunnel.domain):
                tunnel_name = tunnel.name
                zone_id = self._config.domains.cloudflare.zone_id

        if not tunnel_name:
            raise DomainNotFoundError(f"No tunnel found for domain '{domain_name}'")

        # Get tunnel ID and account ID
        account_id = (
            self._config.domains.cloudflare.account_id
            if self._config.domains.cloudflare
            else None
        )
        tunnel_id = None

        if account_id and tunnel_name:
            tunnel_id = await self._tunnel_orchestrator.get_tunnel_id_by_name(
                tunnel_name, account_id
            )

        if not tunnel_id:
            raise DomainNotFoundError(f"Tunnel ID not found for tunnel '{tunnel_name}'")

        # Disable domain using orchestrator
        return await self._tunnel_orchestrator.disable_domain(
            domain_name, tunnel_id, account_id, instance_name, tunnel_name, zone_id
        )
