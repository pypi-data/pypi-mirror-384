"""
Dependency injection composer for cloudflare domains module.

This composer follows the same pattern as core, instance and repository modules,
centralizing dependency creation and configuration.
"""

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.core.infrastructure.driving_adapter.cli.composer import CoreComposer
from dooservice.domains.cloudflare.application.use_cases.domain_disable import (
    DomainDisableUseCase,
)
from dooservice.domains.cloudflare.application.use_cases.domain_enable import (
    DomainEnableUseCase,
)
from dooservice.domains.cloudflare.application.use_cases.domain_sync import (
    DomainSyncUseCase,
)
from dooservice.domains.cloudflare.application.use_cases.tunnel_delete import (
    TunnelDeleteUseCase,
)
from dooservice.domains.cloudflare.application.use_cases.tunnel_init import (
    TunnelInitUseCase,
)
from dooservice.domains.cloudflare.domain.services.tunnel_orchestrator import (
    TunnelOrchestrator,
)
from dooservice.domains.cloudflare.infrastructure.driven_adapter.cloudflare_api.cloudflare_client import (  # noqa: E501
    CloudflareAPIClient,
)
from dooservice.domains.cloudflare.infrastructure.driven_adapter.docker_network.docker_network_adapter import (  # noqa: E501
    DockerNetworkAdapter,
)
from dooservice.domains.cloudflare.infrastructure.implementation.cloudflare_dns_repository import (  # noqa: E501
    CloudflareDNSRepository,
)
from dooservice.domains.cloudflare.infrastructure.implementation.cloudflare_tunnel_repository import (  # noqa: E501
    CloudflareTunnelRepository,
)
from dooservice.domains.cloudflare.infrastructure.implementation.docker_tunnel_repository import (  # noqa: E501
    DockerTunnelRepositoryImpl,
)


class CloudflareComposer:
    """Dependency injection composer for cloudflare module."""

    def __init__(self, config_path: str = "dooservice.yml"):
        self._config_path = config_path
        self._core_composer = CoreComposer()
        self._config = None

    def get_configuration(self) -> DooServiceConfiguration:
        """Get loaded configuration."""
        if self._config is None:
            load_config = self._core_composer.get_load_configuration_use_case()
            self._config = load_config.execute(self._config_path)
        return self._config

    def _create_cloudflare_api_client(self, config: DooServiceConfiguration):
        """Create Cloudflare API client."""
        if not config.domains.cloudflare:
            raise ValueError("Cloudflare configuration not found")

        return CloudflareAPIClient(config.domains.cloudflare.api_token)

    def _create_tunnel_orchestrator(self, config: DooServiceConfiguration):
        """Create tunnel orchestrator with all dependencies."""
        api_client = self._create_cloudflare_api_client(config)

        # Create repositories
        tunnel_repository = CloudflareTunnelRepository(api_client)
        dns_repository = CloudflareDNSRepository(api_client)

        docker_adapter = DockerNetworkAdapter()
        docker_repository = DockerTunnelRepositoryImpl(docker_adapter)

        return TunnelOrchestrator(
            tunnel_repository, dns_repository, docker_repository, config
        )

    def get_tunnel_init_use_case(self):
        """Get TunnelInit use case."""
        config = self.get_configuration()
        orchestrator = self._create_tunnel_orchestrator(config)
        return TunnelInitUseCase(orchestrator, config)

    def get_tunnel_delete_use_case(self):
        """Get TunnelDelete use case."""
        config = self.get_configuration()
        orchestrator = self._create_tunnel_orchestrator(config)
        return TunnelDeleteUseCase(orchestrator, config)

    def get_domain_enable_use_case(self):
        """Get DomainEnable use case."""
        config = self.get_configuration()
        orchestrator = self._create_tunnel_orchestrator(config)
        return DomainEnableUseCase(orchestrator, config)

    def get_domain_disable_use_case(self):
        """Get DomainDisable use case."""
        config = self.get_configuration()
        orchestrator = self._create_tunnel_orchestrator(config)
        return DomainDisableUseCase(orchestrator, config)

    def get_domain_sync_use_case(self):
        """Get DomainSync use case."""
        config = self.get_configuration()
        orchestrator = self._create_tunnel_orchestrator(config)
        return DomainSyncUseCase(orchestrator, config)

    def get_tunnel_repository(self):
        """Get tunnel repository."""
        config = self.get_configuration()
        api_client = self._create_cloudflare_api_client(config)
        return CloudflareTunnelRepository(api_client)

    def get_docker_tunnel_repository(self):
        """Get docker tunnel repository."""
        docker_adapter = DockerNetworkAdapter()
        return DockerTunnelRepositoryImpl(docker_adapter)

    def get_load_configuration_use_case(self):
        """Get LoadConfiguration use case."""
        return self._core_composer.get_load_configuration_use_case()
