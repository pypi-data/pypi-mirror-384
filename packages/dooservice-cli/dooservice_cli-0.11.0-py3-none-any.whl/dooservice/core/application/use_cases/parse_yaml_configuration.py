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
        try:
            with self._messenger.spinner_context(
                "Parsing YAML configuration"
            ) as spinner:
                configuration = self._repository.parse_yaml_content(yaml_content)
                spinner.stop("YAML configuration parsed successfully", success=True)

            if validate:
                with self._messenger.spinner_context(
                    "Validating parsed configuration"
                ) as spinner:
                    is_valid = self._validator.validate(configuration)

                    if not is_valid:
                        errors = self._validator.get_validation_errors()
                        spinner.stop("Configuration validation failed", success=False)
                        for error in errors:
                            self._messenger.error_with_icon(f"  {error}")
                        raise ConfigurationValidationException(
                            "Configuration validation failed", errors
                        )

                    spinner.stop("Configuration validation passed", success=True)

            return configuration

        except Exception as e:
            if not isinstance(e, ConfigurationValidationException):
                self._messenger.error_with_icon(
                    f"Error parsing YAML configuration: {str(e)}"
                )
            raise
