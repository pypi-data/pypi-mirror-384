from dooservice.core.application.use_cases.load_configuration import LoadConfiguration
from dooservice.core.application.use_cases.parse_yaml_configuration import (
    ParseYamlConfiguration,
)
from dooservice.core.application.use_cases.save_configuration import SaveConfiguration
from dooservice.core.application.use_cases.validate_configuration import (
    ValidateConfiguration,
)
from dooservice.core.domain.services.configuration_validator import (
    ConfigurationValidator,
)
from dooservice.core.infrastructure.implementation.yaml_configuration_repository import (  # noqa: E501
    YamlConfigurationRepository,
)
from dooservice.shared.messaging import ClickMessenger


class CoreComposer:
    """Dependency injection composer for core module."""

    def __init__(self):
        self._repository = YamlConfigurationRepository()
        self._validator = ConfigurationValidator()
        self._messenger = ClickMessenger()

    def get_load_configuration_use_case(self) -> LoadConfiguration:
        return LoadConfiguration(
            repository=self._repository,
            validator=self._validator,
            messenger=self._messenger,
        )

    def get_save_configuration_use_case(self) -> SaveConfiguration:
        return SaveConfiguration(
            repository=self._repository,
            validator=self._validator,
            messenger=self._messenger,
        )

    def get_validate_configuration_use_case(self) -> ValidateConfiguration:
        return ValidateConfiguration(
            validator=self._validator, messenger=self._messenger
        )

    def get_parse_yaml_configuration_use_case(self) -> ParseYamlConfiguration:
        return ParseYamlConfiguration(
            repository=self._repository,
            validator=self._validator,
            messenger=self._messenger,
        )
