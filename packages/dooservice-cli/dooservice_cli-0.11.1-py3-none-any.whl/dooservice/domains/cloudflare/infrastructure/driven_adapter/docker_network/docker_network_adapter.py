"""Docker network adapter for tunnel operations."""

from typing import Dict, List

import docker
from dooservice.domains.cloudflare.domain.exceptions.tunnel_exceptions import (
    DockerNetworkError,
)


class DockerNetworkAdapter:
    """Docker adapter for network and container operations."""

    def __init__(self):
        try:
            self._client = docker.from_env()
        except Exception as e:  # noqa: BLE001
            raise DockerNetworkError(f"Failed to connect to Docker: {str(e)}") from e

    async def create_network(self, network_name: str) -> bool:
        """Create Docker network.

        Args:
            network_name: Name of the network to create

        Returns:
            True if network was created successfully

        Raises:
            DockerNetworkError: If network creation fails
        """
        try:
            # Check if network already exists
            if self._network_exists(network_name):
                return True

            self._client.networks.create(network_name, driver="bridge")
            return True

        except Exception as e:  # noqa: BLE001
            raise DockerNetworkError(
                f"Failed to create network '{network_name}': {str(e)}"
            ) from e

    async def delete_network(self, network_name: str) -> bool:
        """Delete Docker network.

        Args:
            network_name: Name of the network to delete

        Returns:
            True if network was deleted successfully

        Raises:
            DockerNetworkError: If network deletion fails
        """
        try:
            if not self._network_exists(network_name):
                return True

            network = self._client.networks.get(network_name)
            network.remove()
            return True

        except Exception as e:  # noqa: BLE001
            raise DockerNetworkError(
                f"Failed to delete network '{network_name}': {str(e)}"
            ) from e

    async def connect_container_to_network(
        self, container_name: str, network_name: str
    ) -> bool:
        """Connect container to network.

        Args:
            container_name: Name of the container
            network_name: Name of the network

        Returns:
            True if container was connected successfully

        Raises:
            DockerNetworkError: If connection fails
        """
        try:
            container = self._client.containers.get(container_name)
            network = self._client.networks.get(network_name)

            # Check if already connected
            if container.id in [c.id for c in network.containers]:
                return True

            network.connect(container)
            return True

        except docker.errors.NotFound as e:
            raise DockerNetworkError(
                f"Container '{container_name}' or network '{network_name}' not found"
            ) from e
        except Exception as e:  # noqa: BLE001
            raise DockerNetworkError(
                f"Failed to connect container '{container_name}' to network "
                f"'{network_name}': {str(e)}"
            ) from e

    async def disconnect_container_from_network(
        self, container_name: str, network_name: str
    ) -> bool:
        """Disconnect container from network.

        Args:
            container_name: Name of the container
            network_name: Name of the network

        Returns:
            True if container was disconnected successfully

        Raises:
            DockerNetworkError: If disconnection fails
        """
        try:
            container = self._client.containers.get(container_name)
            network = self._client.networks.get(network_name)

            # Check if connected
            if container.id not in [c.id for c in network.containers]:
                return True

            network.disconnect(container)
            return True

        except docker.errors.NotFound:
            # Container or network doesn't exist, consider it disconnected
            return True
        except Exception as e:  # noqa: BLE001
            raise DockerNetworkError(
                f"Failed to disconnect container '{container_name}' from network "
                f"'{network_name}': {str(e)}"
            ) from e

    async def start_cloudflared_container(
        self, tunnel_name: str, tunnel_token: str, network_name: str
    ) -> str:
        """Start cloudflared tunnel container.

        Args:
            tunnel_name: Name of the tunnel
            tunnel_token: Cloudflare tunnel token
            network_name: Network to connect to

        Returns:
            Container ID

        Raises:
            DockerNetworkError: If container startup fails
        """
        try:
            container_name = f"cloudflared_{tunnel_name}"

            # Remove existing container if it exists
            try:
                existing_container = self._client.containers.get(container_name)
                existing_container.stop()
                existing_container.remove()
            except docker.errors.NotFound:
                pass

            # Create and start the container
            container = self._client.containers.run(
                image="cloudflare/cloudflared:latest",
                command=f"tunnel run --token {tunnel_token}",
                name=container_name,
                network=network_name,
                restart_policy={"Name": "unless-stopped"},
                detach=True,
                remove=False,
            )

            return container.id

        except Exception as e:  # noqa: BLE001
            raise DockerNetworkError(
                f"Failed to start cloudflared container for tunnel "
                f"'{tunnel_name}': {str(e)}"
            ) from e

    async def stop_cloudflared_container(self, tunnel_name: str) -> bool:
        """Stop cloudflared tunnel container.

        Args:
            tunnel_name: Name of the tunnel

        Returns:
            True if container was stopped successfully

        Raises:
            DockerNetworkError: If container stop fails
        """
        try:
            container_name = f"cloudflared_{tunnel_name}"
            container = self._client.containers.get(container_name)
            container.stop()
            container.remove()
            return True

        except docker.errors.NotFound:
            # Container doesn't exist, consider it stopped
            return True
        except Exception as e:  # noqa: BLE001
            raise DockerNetworkError(
                f"Failed to stop cloudflared container for tunnel "
                f"'{tunnel_name}': {str(e)}"
            ) from e

    async def get_container_status(self, tunnel_name: str) -> Dict:
        """Get tunnel container status.

        Args:
            tunnel_name: Name of the tunnel

        Returns:
            Container status information
        """
        try:
            container_name = f"cloudflared_{tunnel_name}"
            container = self._client.containers.get(container_name)

            return {
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "image": (
                    container.image.tags[0]
                    if container.image.tags
                    else container.image.id
                ),
                "created": container.attrs["Created"],
                "started_at": container.attrs.get("State", {}).get("StartedAt"),
            }

        except docker.errors.NotFound:
            return {
                "status": "not_found",
                "message": f"Container for tunnel '{tunnel_name}' not found",
            }

    async def list_networks(self) -> List[str]:
        """List all Docker networks.

        Returns:
            List of network names
        """
        try:
            networks = self._client.networks.list()
            return [network.name for network in networks]

        except Exception as e:  # noqa: BLE001
            raise DockerNetworkError(f"Failed to list networks: {str(e)}") from e

    def _network_exists(self, network_name: str) -> bool:
        """Check if network exists."""
        try:
            self._client.networks.get(network_name)
            return True
        except docker.errors.NotFound:
            return False

    async def get_instance_containers(self, instance_name: str) -> List[str]:
        """Get container names for an instance.

        Args:
            instance_name: Instance name

        Returns:
            List of container names
        """
        try:
            containers = self._client.containers.list(all=True)
            return [
                container.name
                for container in containers
                if instance_name in container.name
            ]

        except Exception as e:  # noqa: BLE001
            raise DockerNetworkError(
                f"Failed to get containers for instance '{instance_name}': {str(e)}"
            ) from e
