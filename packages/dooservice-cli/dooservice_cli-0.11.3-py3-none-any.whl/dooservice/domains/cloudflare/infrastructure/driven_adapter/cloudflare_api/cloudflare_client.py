"""Cloudflare API client adapter."""

from typing import Dict, List, Optional

import httpx

from dooservice.domains.cloudflare.domain.exceptions.tunnel_exceptions import (
    CloudflareAPIError,
)


class CloudflareAPIClient:
    """Cloudflare API client for tunnel and DNS operations."""

    def __init__(self, api_token: str):
        self._api_token = api_token
        self._base_url = "https://api.cloudflare.com/client/v4"
        self._headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    async def create_tunnel(self, name: str, account_id: str) -> Dict:
        """Create a new tunnel via Cloudflare API.

        Args:
            name: Tunnel name
            account_id: Cloudflare account ID

        Returns:
            Tunnel data from API response

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = f"{self._base_url}/accounts/{account_id}/cfd_tunnel"
        data = {"name": name, "tunnel_secret": self._generate_tunnel_secret()}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=self._headers)
                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    raise CloudflareAPIError(
                        f"Tunnel creation failed: {result.get('errors', [])}"
                    )

                return result["result"]

            except httpx.HTTPError as e:
                raise CloudflareAPIError(f"HTTP error creating tunnel: {str(e)}") from e

    async def get_tunnel(self, tunnel_id: str, account_id: str) -> Optional[Dict]:
        """Get tunnel information.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID

        Returns:
            Tunnel data if found, None otherwise

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = f"{self._base_url}/accounts/{account_id}/cfd_tunnel/{tunnel_id}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._headers)

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    raise CloudflareAPIError(
                        f"Failed to get tunnel: {result.get('errors', [])}"
                    )

                return result["result"]

            except httpx.HTTPError as e:
                raise CloudflareAPIError(f"HTTP error getting tunnel: {str(e)}") from e

    async def list_tunnels(self, account_id: str) -> List[Dict]:
        """List all tunnels for account.

        Args:
            account_id: Cloudflare account ID

        Returns:
            List of tunnel data

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = f"{self._base_url}/accounts/{account_id}/cfd_tunnel"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._headers)
                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    raise CloudflareAPIError(
                        f"Failed to list tunnels: {result.get('errors', [])}"
                    )

                return result["result"]

            except httpx.HTTPError as e:
                raise CloudflareAPIError(f"HTTP error listing tunnels: {str(e)}") from e

    async def configure_tunnel(
        self, tunnel_id: str, account_id: str, configuration: Dict
    ) -> bool:
        """Configure tunnel ingress rules.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID
            configuration: Tunnel configuration

        Returns:
            True if configured successfully

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = (
            f"{self._base_url}/accounts/{account_id}"
            f"/cfd_tunnel/{tunnel_id}/configurations"
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    url, json=configuration, headers=self._headers
                )
                response.raise_for_status()
                result = response.json()

                return result.get("success", False)

            except httpx.HTTPError as e:
                raise CloudflareAPIError(
                    f"HTTP error configuring tunnel: {str(e)}"
                ) from e

    async def get_tunnel_token(self, tunnel_id: str, account_id: str) -> str:
        """Get tunnel token.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID

        Returns:
            Tunnel token

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = f"{self._base_url}/accounts/{account_id}/cfd_tunnel/{tunnel_id}/token"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._headers)
                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    raise CloudflareAPIError(
                        f"Failed to get tunnel token: {result.get('errors', [])}"
                    )

                return result["result"]

            except httpx.HTTPError as e:
                raise CloudflareAPIError(
                    f"HTTP error getting tunnel token: {str(e)}"
                ) from e

    async def delete_tunnel(self, tunnel_id: str, account_id: str) -> bool:
        """Delete tunnel.

        Args:
            tunnel_id: Tunnel ID
            account_id: Account ID

        Returns:
            True if deleted successfully

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = f"{self._base_url}/accounts/{account_id}/cfd_tunnel/{tunnel_id}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(url, headers=self._headers)
                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    raise CloudflareAPIError(
                        f"Failed to delete tunnel: {result.get('errors', [])}"
                    )

                return result.get("success", False)

            except httpx.HTTPError as e:
                raise CloudflareAPIError(f"HTTP error deleting tunnel: {str(e)}") from e

    async def get_tunnel_configuration(
        self, tunnel_id: str, account_id: str
    ) -> Optional[Dict]:
        """Get tunnel configuration.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID

        Returns:
            Tunnel configuration if found, None otherwise

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = (
            f"{self._base_url}/accounts/{account_id}"
            f"/cfd_tunnel/{tunnel_id}/configurations"
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._headers)

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    return None

                return result.get("result")

            except httpx.HTTPError as e:
                raise CloudflareAPIError(
                    f"HTTP error getting tunnel configuration: {str(e)}"
                ) from e

    async def update_tunnel_configuration(
        self, tunnel_id: str, account_id: str, configuration: Dict
    ) -> bool:
        """Update tunnel configuration.

        Args:
            tunnel_id: Tunnel ID
            account_id: Cloudflare account ID
            configuration: New tunnel configuration

        Returns:
            True if updated successfully

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = (
            f"{self._base_url}/accounts/{account_id}"
            f"/cfd_tunnel/{tunnel_id}/configurations"
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    url, json=configuration, headers=self._headers
                )
                response.raise_for_status()
                result = response.json()

                return result.get("success", False)

            except httpx.HTTPError as e:
                raise CloudflareAPIError(
                    f"HTTP error updating tunnel configuration: {str(e)}"
                ) from e

    async def create_dns_record(self, zone_id: str, record_data: Dict) -> Dict:
        """Create DNS record.

        Args:
            zone_id: Zone ID
            record_data: DNS record data

        Returns:
            Created DNS record data

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = f"{self._base_url}/zones/{zone_id}/dns_records"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, json=record_data, headers=self._headers
                )
                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    raise CloudflareAPIError(
                        f"DNS record creation failed: {result.get('errors', [])}"
                    )

                return result["result"]

            except httpx.HTTPError as e:
                raise CloudflareAPIError(
                    f"HTTP error creating DNS record: {str(e)}"
                ) from e

    async def get_dns_record(self, zone_id: str, record_name: str) -> Optional[Dict]:
        """Get DNS record by name.

        Args:
            zone_id: Zone ID
            record_name: DNS record name

        Returns:
            DNS record data if found

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = f"{self._base_url}/zones/{zone_id}/dns_records"
        params = {"name": record_name}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, headers=self._headers)
                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    raise CloudflareAPIError(
                        f"Failed to get DNS records: {result.get('errors', [])}"
                    )

                records = result["result"]
                return records[0] if records else None

            except httpx.HTTPError as e:
                raise CloudflareAPIError(
                    f"HTTP error getting DNS record: {str(e)}"
                ) from e

    async def delete_dns_record(self, zone_id: str, record_id: str) -> bool:
        """Delete DNS record.

        Args:
            zone_id: Zone ID
            record_id: DNS record ID

        Returns:
            True if deleted successfully

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = f"{self._base_url}/zones/{zone_id}/dns_records/{record_id}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(url, headers=self._headers)
                response.raise_for_status()
                result = response.json()

                return result.get("success", False)

            except httpx.HTTPError as e:
                raise CloudflareAPIError(
                    f"HTTP error deleting DNS record: {str(e)}"
                ) from e

    async def list_dns_records(self, zone_id: str, tunnel_id: str) -> List[Dict]:
        """List DNS records pointing to a specific tunnel.

        Args:
            zone_id: Zone ID
            tunnel_id: Tunnel ID to filter by

        Returns:
            List of DNS records

        Raises:
            CloudflareAPIError: If API request fails
        """
        url = f"{self._base_url}/zones/{zone_id}/dns_records"
        tunnel_domain = f"{tunnel_id}.cfargotunnel.com"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._headers)
                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    raise CloudflareAPIError(
                        f"Failed to list DNS records: {result.get('errors', [])}"
                    )

                # Filter records that point to this tunnel
                return [
                    record
                    for record in result["result"]
                    if record.get("content") == tunnel_domain
                ]

            except httpx.HTTPError as e:
                raise CloudflareAPIError(
                    f"HTTP error listing DNS records: {str(e)}"
                ) from e

    def _generate_tunnel_secret(self) -> str:
        """Generate tunnel secret (32 random bytes base64 encoded)."""
        import base64
        import secrets

        return base64.b64encode(secrets.token_bytes(32)).decode("utf-8")
