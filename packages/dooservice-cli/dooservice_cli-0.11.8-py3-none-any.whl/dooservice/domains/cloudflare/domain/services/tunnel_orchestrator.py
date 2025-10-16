"""Tunnel orchestration service."""

from typing import Dict, Optional

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.domains.cloudflare.domain.entities.domain import (
    DomainConfiguration,
    DomainStatus,
    DomainSyncResult,
)
from dooservice.domains.cloudflare.domain.entities.tunnel import (
    TunnelConfig,
    TunnelConfiguration,
    TunnelDNSRecord,
    TunnelIngress,
)
from dooservice.domains.cloudflare.domain.exceptions.domain_exceptions import (
    DomainSyncError,
)
from dooservice.domains.cloudflare.domain.exceptions.tunnel_exceptions import (
    TunnelCreationError,
)
from dooservice.domains.cloudflare.domain.repositories.dns_repository import (
    DNSRepository,
)
from dooservice.domains.cloudflare.domain.repositories.docker_repository import (
    DockerTunnelRepository,
)
from dooservice.domains.cloudflare.domain.repositories.tunnel_repository import (
    TunnelRepository,
)


class TunnelOrchestrator:
    """Service for orchestrating tunnel operations."""

    def __init__(
        self,
        tunnel_repository: TunnelRepository,
        dns_repository: DNSRepository,
        docker_repository: DockerTunnelRepository,
        config: Optional[DooServiceConfiguration] = None,
    ):
        self._tunnel_repository = tunnel_repository
        self._dns_repository = dns_repository
        self._docker_repository = docker_repository
        self._config = config

    async def initialize_tunnel(
        self, tunnel_name: str, account_id: str, zone_id: str, domain: str
    ) -> TunnelConfig:
        """Initialize a new tunnel with Docker network.

        Args:
            tunnel_name: Name of the tunnel
            account_id: Cloudflare account ID
            zone_id: Cloudflare zone ID
            domain: Root domain

        Returns:
            Tunnel configuration

        Raises:
            TunnelCreationError: If tunnel creation fails
        """
        try:
            # Create tunnel in Cloudflare
            tunnel_config = await self._tunnel_repository.create_tunnel(
                tunnel_name, account_id
            )

            # Create Docker network for the tunnel
            network_name = f"tunnel_{tunnel_name}"
            await self._docker_repository.create_tunnel_network(network_name)

            # Get tunnel token
            tunnel_token = await self._tunnel_repository.get_tunnel_token(
                tunnel_config.tunnel_id, account_id
            )

            # Start cloudflared container
            await self._docker_repository.start_tunnel_container(
                tunnel_name, tunnel_token, network_name
            )

            return tunnel_config

        except Exception as e:  # noqa: BLE001
            raise TunnelCreationError(f"Failed to initialize tunnel: {str(e)}") from e

    async def get_tunnel_id_by_name(self, tunnel_name: str, account_id: str) -> str:
        """Get tunnel ID by name.

        Args:
            tunnel_name: Name of the tunnel
            account_id: Cloudflare account ID

        Returns:
            Tunnel ID
        """
        tunnels = await self._tunnel_repository.list_tunnels(account_id)
        active_tunnel = None
        fallback_tunnel = None

        for tunnel in tunnels:
            if tunnel.name == tunnel_name:
                if len(tunnel.connections) > 0:
                    # Prefer tunnel with active connections
                    active_tunnel = tunnel
                    break
                if fallback_tunnel is None:
                    # Keep first matching tunnel as fallback
                    fallback_tunnel = tunnel

        if active_tunnel:
            return active_tunnel.tunnel_id
        if fallback_tunnel:
            return fallback_tunnel.tunnel_id

        raise TunnelCreationError(f"Tunnel '{tunnel_name}' not found")

    async def configure_domain(
        self, domain_config: DomainConfiguration, account_id: str
    ) -> bool:
        """Configure domain with tunnel ingress and DNS.

        Args:
            domain_config: Domain configuration
            account_id: Cloudflare account ID

        Returns:
            True if configured successfully
        """
        try:
            # Get current tunnel configuration to preserve existing domains
            current_config = await self._tunnel_repository.get_tunnel_configuration(
                domain_config.tunnel_id, account_id
            )

            # Create new ingress rule for this domain
            new_ingress_rule = TunnelIngress(
                hostname=domain_config.domain_name,
                service=f"http://web_{domain_config.instance_name}:8069",
            )

            # Build ingress list with existing rules + new rule
            ingress_rules = []
            if current_config and current_config.ingress:
                # Keep existing rules that don't match this domain (avoid duplicates)
                # Also filter out rules with empty/None hostname (catch-all rules)
                ingress_rules.extend(
                    rule
                    for rule in current_config.ingress
                    if rule.hostname and rule.hostname != domain_config.domain_name
                )

            # Add the new rule
            ingress_rules.append(new_ingress_rule)

            # Configure tunnel with all ingress rules
            tunnel_configuration = TunnelConfiguration(
                tunnel_id=domain_config.tunnel_id,
                ingress=ingress_rules,
                warp_routing=(current_config.warp_routing if current_config else None),
                origin_request=(
                    current_config.origin_request if current_config else None
                ),
            )

            await self._tunnel_repository.configure_tunnel(
                domain_config.tunnel_id,
                account_id,
                tunnel_configuration,
            )

            # Create DNS record
            dns_record = TunnelDNSRecord(
                record_id=None,
                zone_id=domain_config.zone_id,
                name=domain_config.domain_name,
                type="CNAME",
                content=f"{domain_config.tunnel_id}.cfargotunnel.com",
            )

            created_record = await self._dns_repository.create_dns_record(dns_record)
            domain_config.dns_record_id = created_record.record_id

            return True

        except Exception as e:  # noqa: BLE001
            domain_config.status = DomainStatus.ERROR
            domain_config.error_message = str(e)
            return False

    async def sync_domain_to_instance(
        self, domain_name: str, instance_name: str, tunnel_name: str
    ) -> DomainSyncResult:
        """Sync domain to instance by connecting to tunnel network.

        Args:
            domain_name: Domain name
            instance_name: Instance name
            tunnel_name: Tunnel name

        Returns:
            Sync result

        Raises:
            DomainSyncError: If synchronization fails
        """
        try:
            network_name = f"tunnel_{tunnel_name}"

            # Connect instance to tunnel network
            connected = await self._docker_repository.connect_instance_to_network(
                instance_name, network_name
            )

            if not connected:
                raise DomainSyncError(
                    f"Failed to connect instance {instance_name} to network "
                    f"{network_name}"
                )

            return DomainSyncResult(
                domain_name=domain_name,
                success=True,
                message="Domain successfully synchronized with instance",
                network_connected=True,
                dns_created=True,  # Assumed already created
                tunnel_configured=True,  # Assumed already configured
            )

        except Exception as e:  # noqa: BLE001
            return DomainSyncResult(
                domain_name=domain_name,
                success=False,
                message=f"Failed to sync domain: {str(e)}",
                network_connected=False,
            )

    async def connect_instance_to_tunnel_network(
        self, instance_name: str, tunnel_name: str
    ) -> bool:
        """Connect instance to tunnel network.

        Args:
            instance_name: Name of the instance
            tunnel_name: Name of the tunnel

        Returns:
            True if connected successfully
        """
        try:
            network_name = f"tunnel_{tunnel_name}"

            # Connect instance containers to tunnel network
            return await self._docker_repository.connect_instance_to_network(
                instance_name, network_name
            )
        except Exception:  # noqa: BLE001
            return False

    async def get_tunnel_status(self, tunnel_name: str) -> Dict:
        """Get tunnel status.

        Args:
            tunnel_name: Tunnel name

        Returns:
            Tunnel status information
        """
        return await self._docker_repository.get_tunnel_container_status(tunnel_name)

    async def disable_domain(
        self,
        domain_name: str,
        tunnel_id: str,
        account_id: str,
        instance_name: str,
        tunnel_name: str,
        zone_id: str,
    ) -> bool:
        """Disable domain by removing it from tunnel configuration and DNS record.

        Args:
            domain_name: Domain name to disable
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID
            instance_name: Instance name
            tunnel_name: Tunnel name
            zone_id: Zone ID for DNS

        Returns:
            True if disabled successfully
        """
        try:
            # Remove domain from tunnel configuration
            tunnel_success = await self._tunnel_repository.remove_domain_from_tunnel(
                tunnel_id, account_id, domain_name
            )

            # Get and delete DNS record
            try:
                dns_record = await self._dns_repository.get_dns_record(
                    zone_id, domain_name
                )
                if dns_record and dns_record.record_id:
                    await self._dns_repository.delete_dns_record(
                        zone_id, dns_record.record_id
                    )
            except Exception:  # noqa: BLE001, S110
                # DNS record deletion failed, but continue with cleanup
                pass

            # Disconnect instance from tunnel network
            if tunnel_success:
                try:
                    network_name = f"tunnel_{tunnel_name}"
                    await self._docker_repository.disconnect_instance_from_network(
                        instance_name, network_name
                    )
                except Exception:  # noqa: BLE001, S110
                    # Network disconnection failed, but continue
                    pass

            # Return true if at least tunnel configuration was removed
            return tunnel_success

        except Exception:  # noqa: BLE001
            return False

    async def delete_tunnel_dns_records(self, tunnel_id: str, account_id: str) -> bool:
        """Delete all DNS records associated with a tunnel.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID

        Returns:
            True if all records were deleted successfully
        """
        try:
            # Get all zones from configuration
            if not self._config.domains.cloudflare:
                return True

            success = True

            # Get zone ID from cloudflare configuration
            zone_id = self._config.domains.cloudflare.zone_id

            # Find and delete records pointing to this tunnel
            if zone_id:
                try:
                    # Get all DNS records for this tunnel
                    tunnel_records = await self._dns_repository.get_tunnel_dns_records(
                        zone_id, tunnel_id
                    )

                    # Delete each record
                    for record in tunnel_records:
                        try:
                            await self._dns_repository.delete_dns_record(
                                zone_id, record.record_id
                            )
                        except Exception:  # noqa: BLE001  # noqa: BLE001  # noqa: BLE001  # noqa: BLE001
                            success = False

                except Exception:  # noqa: BLE001  # noqa: BLE001  # noqa: BLE001
                    success = False

            return success

        except Exception:  # noqa: BLE001
            return False

    async def delete_tunnel_complete(
        self, tunnel_id: str, account_id: str, tunnel_name: str
    ) -> bool:
        """Delete tunnel completely including all associated DNS records.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID
            tunnel_name: Tunnel name

        Returns:
            True if deleted successfully
        """
        try:
            # Stop tunnel container first
            await self._docker_repository.stop_tunnel_container(tunnel_name)

            # Delete all DNS records associated with this tunnel
            await self.delete_tunnel_dns_records(tunnel_id, account_id)

            # Delete the tunnel itself
            return await self._tunnel_repository.delete_tunnel(tunnel_id, account_id)

        except Exception:  # noqa: BLE001
            return False

    async def restart_tunnel_container(self, tunnel_name: str) -> bool:
        """Restart tunnel container to apply configuration changes.

        Args:
            tunnel_name: Tunnel name

        Returns:
            True if restarted successfully
        """
        try:
            if (
                not self._config
                or not self._config.domains
                or not self._config.domains.cloudflare
            ):
                return False

            account_id = self._config.domains.cloudflare.account_id

            # Get tunnel ID and token
            tunnel_id = await self.get_tunnel_id_by_name(tunnel_name, account_id)
            tunnel_token = await self._tunnel_repository.get_tunnel_token(
                tunnel_id, account_id
            )

            # Stop and start the tunnel container
            await self._docker_repository.stop_tunnel_container(tunnel_name)
            await self._docker_repository.start_tunnel_container(
                tunnel_name, tunnel_token, f"tunnel_{tunnel_name}"
            )
            return True
        except Exception:  # noqa: BLE001
            return False
