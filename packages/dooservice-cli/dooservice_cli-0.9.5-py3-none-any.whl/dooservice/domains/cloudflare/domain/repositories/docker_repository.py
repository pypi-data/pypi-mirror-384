"""Docker repository interface for tunnel operations."""

from abc import ABC, abstractmethod
from typing import Dict, List


class DockerTunnelRepository(ABC):
    """Abstract repository for Docker tunnel operations."""

    @abstractmethod
    async def create_tunnel_network(self, network_name: str) -> bool:
        """Create Docker network for tunnel.

        Args:
            network_name: Network name

        Returns:
            True if network created successfully
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete_tunnel_network(self, network_name: str) -> bool:
        """Delete Docker network for tunnel.

        Args:
            network_name: Network name

        Returns:
            True if network deleted successfully
        """
        raise NotImplementedError()

    @abstractmethod
    async def connect_instance_to_network(
        self, instance_name: str, network_name: str
    ) -> bool:
        """Connect instance containers to tunnel network.

        Args:
            instance_name: Instance name
            network_name: Network name

        Returns:
            True if connected successfully
        """
        raise NotImplementedError()

    @abstractmethod
    async def disconnect_instance_from_network(
        self, instance_name: str, network_name: str
    ) -> bool:
        """Disconnect instance containers from tunnel network.

        Args:
            instance_name: Instance name
            network_name: Network name

        Returns:
            True if disconnected successfully
        """
        raise NotImplementedError()

    @abstractmethod
    async def start_tunnel_container(
        self, tunnel_name: str, tunnel_token: str, network_name: str
    ) -> str:
        """Start cloudflared tunnel container.

        Args:
            tunnel_name: Tunnel name
            tunnel_token: Tunnel token
            network_name: Network name

        Returns:
            Container ID
        """
        raise NotImplementedError()

    @abstractmethod
    async def stop_tunnel_container(self, tunnel_name: str) -> bool:
        """Stop cloudflared tunnel container.

        Args:
            tunnel_name: Tunnel name

        Returns:
            True if stopped successfully
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_tunnel_container_status(self, tunnel_name: str) -> Dict:
        """Get tunnel container status.

        Args:
            tunnel_name: Tunnel name

        Returns:
            Container status information
        """
        raise NotImplementedError()

    @abstractmethod
    async def list_networks(self) -> List[str]:
        """List all Docker networks.

        Returns:
            List of network names
        """
        raise NotImplementedError()
