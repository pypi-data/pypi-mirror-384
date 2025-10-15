from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.core.domain.exceptions.configuration_exceptions import (
    ConfigurationValidationException,
)
from dooservice.core.domain.repositories.configuration_repository import (
    ConfigurationRepository,
)
from dooservice.core.domain.services.configuration_validator import (
    ConfigurationValidator,
)
from dooservice.shared.messaging import MessageInterface


class ParseYamlConfiguration:
    def __init__(
        self,
        repository: ConfigurationRepository,
        validator: ConfigurationValidator,
        messenger: MessageInterface,
    ):
        self._repository = repository
        self._validator = validator
        self._messenger = messenger

    def execute(
        self, yaml_content: str, validate: bool = True
    ) -> DooServiceConfiguration:
        self._messenger.send_info("Parsing YAML configuration...")

        try:
            configuration = self._repository.parse_yaml_content(yaml_content)
            self._messenger.send_success("YAML configuration parsed successfully")

            if validate:
                self._messenger.send_info("Validating parsed configuration...")
                is_valid = self._validator.validate(configuration)

                if not is_valid:
                    errors = self._validator.get_validation_errors()
                    self._messenger.send_error("Configuration validation failed")
                    for error in errors:
                        self._messenger.send_error(f"  - {error}")
                    raise ConfigurationValidationException(
                        "Configuration validation failed", errors
                    )

                self._messenger.send_success("Configuration validation passed")

            return configuration

        except Exception as e:
            if not isinstance(e, ConfigurationValidationException):
                self._messenger.send_error(
                    f"Error parsing YAML configuration: {str(e)}"
                )
            raise
