"""Tunnel domain exceptions."""


class TunnelError(Exception):
    """Base exception for tunnel operations."""


class TunnelCreationError(TunnelError):
    """Exception raised when tunnel creation fails."""


class TunnelConfigurationError(TunnelError):
    """Exception raised when tunnel configuration fails."""


class TunnelNotFoundError(TunnelError):
    """Exception raised when tunnel is not found."""


class CloudflareAPIError(TunnelError):
    """Exception raised when Cloudflare API call fails."""


class DockerNetworkError(TunnelError):
    """Exception raised when Docker network operations fail."""
