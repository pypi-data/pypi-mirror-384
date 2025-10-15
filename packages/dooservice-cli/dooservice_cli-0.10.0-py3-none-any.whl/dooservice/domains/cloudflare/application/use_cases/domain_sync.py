"""Domain sync use case."""

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.domains.cloudflare.domain.entities.domain import DomainSyncResult
from dooservice.domains.cloudflare.domain.exceptions.domain_exceptions import (
    DomainNotFoundError,
)
from dooservice.domains.cloudflare.domain.services.tunnel_orchestrator import (
    TunnelOrchestrator,
)


class DomainSyncUseCase:
    """Use case for synchronizing domain with instance."""

    def __init__(
        self,
        tunnel_orchestrator: TunnelOrchestrator,
        config: DooServiceConfiguration,
    ):
        self._tunnel_orchestrator = tunnel_orchestrator
        self._config = config

    async def execute(self, domain_name: str) -> DomainSyncResult:
        """Execute domain synchronization.

        Args:
            domain_name: Domain name to sync

        Returns:
            Synchronization result

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

        if self._config.domains.cloudflare and self._config.domains.cloudflare.tunnel:
            tunnel = self._config.domains.cloudflare.tunnel
            if base_domain.name.endswith(tunnel.domain):
                tunnel_name = tunnel.name

        if not tunnel_name:
            return DomainSyncResult(
                domain_name=domain_name,
                success=False,
                message=f"No tunnel found for domain '{domain_name}'",
            )

        # Sync domain to instance
        return await self._tunnel_orchestrator.sync_domain_to_instance(
            domain_name, instance_name, tunnel_name
        )
