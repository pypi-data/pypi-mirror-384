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
            with self._messenger.spinner_context(
                "Validating configuration before saving"
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

        path = Path(file_path)

        try:
            with self._messenger.spinner_context(
                f"Saving configuration to {Path(file_path).name}"
            ) as spinner:
                self._repository.save_to_file(configuration, path)
                spinner.stop("Configuration saved successfully", success=True)

        except Exception as e:
            self._messenger.error_with_icon(f"Error saving configuration: {str(e)}")
            raise
