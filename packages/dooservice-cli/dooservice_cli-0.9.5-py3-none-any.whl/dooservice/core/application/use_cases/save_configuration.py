from pathlib import Path

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


class SaveConfiguration:
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
        self,
        configuration: DooServiceConfiguration,
        file_path: str,
        validate: bool = True,
    ) -> None:
        if validate:
            self._messenger.send_info("Validating configuration before saving...")
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

        path = Path(file_path)
        self._messenger.send_info(f"Saving configuration to: {file_path}")

        try:
            self._repository.save_to_file(configuration, path)
            self._messenger.send_success("Configuration saved successfully")

        except Exception as e:
            self._messenger.send_error(f"Error saving configuration: {str(e)}")
            raise
