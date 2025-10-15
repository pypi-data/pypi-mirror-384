from pathlib import Path

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.core.domain.exceptions.configuration_exceptions import (
    ConfigurationFileNotFoundException,
    ConfigurationValidationException,
)
from dooservice.core.domain.repositories.configuration_repository import (
    ConfigurationRepository,
)
from dooservice.core.domain.services.configuration_validator import (
    ConfigurationValidator,
)
from dooservice.shared.messaging import MessageInterface


class LoadConfiguration:
    def __init__(
        self,
        repository: ConfigurationRepository,
        validator: ConfigurationValidator,
        messenger: MessageInterface,
    ):
        self._repository = repository
        self._validator = validator
        self._messenger = messenger

    def execute(self, file_path: str, validate: bool = True) -> DooServiceConfiguration:
        path = Path(file_path)

        if not path.exists():
            self._messenger.send_error(f"Configuration file not found: {file_path}")
            raise ConfigurationFileNotFoundException(str(path))

        self._messenger.send_info(f"Loading configuration from: {file_path}")

        try:
            configuration = self._repository.load_from_file(path)
            self._messenger.send_success(
                "Configuration loaded and parameters resolved successfully"
            )

            if validate:
                self._messenger.send_info("Validating configuration...")
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
            if not isinstance(
                e,
                (ConfigurationFileNotFoundException, ConfigurationValidationException),
            ):
                self._messenger.send_error(f"Error loading configuration: {str(e)}")
            raise
