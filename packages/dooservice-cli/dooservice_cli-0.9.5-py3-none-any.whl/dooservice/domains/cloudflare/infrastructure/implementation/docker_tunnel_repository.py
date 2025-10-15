"""Docker tunnel repository implementation."""

from typing import Dict, List

from dooservice.domains.cloudflare.domain.repositories.docker_repository import (
    DockerTunnelRepository,
)
from dooservice.domains.cloudflare.infrastructure.driven_adapter.docker_network.docker_network_adapter import (  # noqa: E501
    DockerNetworkAdapter,
)


class DockerTunnelRepositoryImpl(DockerTunnelRepository):
    """Docker tunnel repository implementation."""

    def __init__(self, docker_adapter: DockerNetworkAdapter):
        self._docker_adapter = docker_adapter

    async def create_tunnel_network(self, network_name: str) -> bool:
        """Create Docker network for tunnel."""
        return await self._docker_adapter.create_network(network_name)

    async def delete_tunnel_network(self, network_name: str) -> bool:
        """Delete Docker network for tunnel."""
        return await self._docker_adapter.delete_network(network_name)

    async def connect_instance_to_network(
        self, instance_name: str, network_name: str
    ) -> bool:
        """Connect instance containers to tunnel network."""
        try:
            # Get all containers for the instance
            instance_containers = await self._docker_adapter.get_instance_containers(
                instance_name
            )

            # Connect each container to the network
            for container_name in instance_containers:
                await self._docker_adapter.connect_container_to_network(
                    container_name, network_name
                )

            return True

        except Exception:  # noqa: BLE001
            return False

    async def disconnect_instance_from_network(
        self, instance_name: str, network_name: str
    ) -> bool:
        """Disconnect instance containers from tunnel network."""
        try:
            # Get all containers for the instance
            instance_containers = await self._docker_adapter.get_instance_containers(
                instance_name
            )

            # Disconnect each container from the network
            for container_name in instance_containers:
                await self._docker_adapter.disconnect_container_from_network(
                    container_name, network_name
                )

            return True

        except Exception:  # noqa: BLE001
            return False

    async def start_tunnel_container(
        self, tunnel_name: str, tunnel_token: str, network_name: str
    ) -> str:
        """Start cloudflared tunnel container."""
        return await self._docker_adapter.start_cloudflared_container(
            tunnel_name, tunnel_token, network_name
        )

    async def stop_tunnel_container(self, tunnel_name: str) -> bool:
        """Stop cloudflared tunnel container."""
        return await self._docker_adapter.stop_cloudflared_container(tunnel_name)

    async def get_tunnel_container_status(self, tunnel_name: str) -> Dict:
        """Get tunnel container status."""
        return await self._docker_adapter.get_container_status(tunnel_name)

    async def list_networks(self) -> List[str]:
        """List all Docker networks."""
        return await self._docker_adapter.list_networks()
