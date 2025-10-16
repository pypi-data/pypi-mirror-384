from dooservice.core.application.use_cases.load_configuration import LoadConfiguration
from dooservice.core.infrastructure.driving_adapter.cli.composer import CoreComposer
from dooservice.shared.messaging import MessageInterface


class ConfigurationManager:
    """Configuration management implementation that coordinates dependencies."""

    def __init__(self, messenger: MessageInterface):
        self._messenger = messenger
        self._composer = CoreComposer()

    def get_load_configuration_use_case(self) -> LoadConfiguration:
        """Get the load configuration use case."""
        return self._composer.get_load_configuration_use_case()
