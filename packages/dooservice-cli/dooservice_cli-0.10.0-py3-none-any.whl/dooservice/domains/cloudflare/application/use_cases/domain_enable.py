"""Domain enable use case."""

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.domains.cloudflare.domain.entities.domain import (
    DomainConfiguration,
    DomainStatus,
)
from dooservice.domains.cloudflare.domain.exceptions.domain_exceptions import (
    DomainNotFoundError,
    InstanceNotFoundError,
)
from dooservice.domains.cloudflare.domain.services.tunnel_orchestrator import (
    TunnelOrchestrator,
)


class DomainEnableUseCase:
    """Use case for enabling a domain."""

    def __init__(
        self,
        tunnel_orchestrator: TunnelOrchestrator,
        config: DooServiceConfiguration,
    ):
        self._tunnel_orchestrator = tunnel_orchestrator
        self._config = config

    async def execute(self, domain_name: str) -> bool:
        """Execute domain enabling.

        Args:
            domain_name: Domain name to enable

        Returns:
            True if domain was enabled successfully

        Raises:
            DomainNotFoundError: If domain is not found in configuration
            InstanceNotFoundError: If target instance is not found
        """
        # Find domain in configuration
        if domain_name not in self._config.domains.base_domains:
            raise DomainNotFoundError(
                f"Domain '{domain_name}' not found in configuration"
            )

        base_domain = self._config.domains.base_domains[domain_name]
        instance_name = base_domain.instance

        # Validate instance exists
        if instance_name not in self._config.instances:
            raise InstanceNotFoundError(f"Instance '{instance_name}' not found")

        instance = self._config.instances[instance_name]
        instance_port = int(instance.ports.http) if instance.ports.http else 8071

        # Find tunnel for domain
        tunnel_name = None
        tunnel_id = None
        zone_id = None
        account_id = (
            self._config.domains.cloudflare.account_id
            if self._config.domains.cloudflare
            else None
        )

        if self._config.domains.cloudflare and self._config.domains.cloudflare.tunnel:
            tunnel = self._config.domains.cloudflare.tunnel
            if base_domain.name.endswith(tunnel.domain):
                tunnel_name = tunnel.name
                # Get actual tunnel ID from Cloudflare API
                tunnel_id = await self._tunnel_orchestrator.get_tunnel_id_by_name(
                    tunnel_name, account_id
                )
                zone_id = self._config.domains.cloudflare.zone_id

        if not tunnel_name:
            raise DomainNotFoundError(f"No tunnel found for domain '{domain_name}'")

        # Create domain configuration
        domain_config = DomainConfiguration(
            domain_name=domain_name,
            instance_name=instance_name,
            tunnel_name=tunnel_name,
            instance_port=instance_port,
            status=DomainStatus.PENDING,
            zone_id=zone_id,
            tunnel_id=tunnel_id,
        )

        # Configure domain with tunnel and DNS
        success = await self._tunnel_orchestrator.configure_domain(
            domain_config, account_id
        )

        if success:
            # Connect instance to tunnel network
            network_success = (
                await self._tunnel_orchestrator.connect_instance_to_tunnel_network(
                    instance_name, tunnel_name
                )
            )

            if network_success:
                # Restart tunnel container to apply new configuration
                restart_success = (
                    await self._tunnel_orchestrator.restart_tunnel_container(
                        tunnel_name
                    )
                )

                if restart_success:
                    domain_config.status = DomainStatus.ENABLED
                else:
                    domain_config.status = DomainStatus.ERROR
                    return False
            else:
                domain_config.status = DomainStatus.ERROR
                return False
        else:
            domain_config.status = DomainStatus.ERROR

        return success
