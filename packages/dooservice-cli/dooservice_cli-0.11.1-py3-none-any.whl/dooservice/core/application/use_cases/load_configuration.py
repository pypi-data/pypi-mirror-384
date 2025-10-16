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
            self._messenger.error_with_icon(
                f"Configuration file not found: {file_path}"
            )
            raise ConfigurationFileNotFoundException(str(path))

        try:
            # Use a quick spinner for loading (no show_time for quick operations)
            with self._messenger.spinner_context(
                f"Loading configuration from {Path(file_path).name}"
            ) as spinner:
                configuration = self._repository.load_from_file(path)
                spinner.stop("Configuration loaded successfully", success=True)

            if validate:
                # Use a different animation style for validation
                with self._messenger.spinner_context(
                    "Validating configuration"
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
            if not isinstance(
                e,
                (ConfigurationFileNotFoundException, ConfigurationValidationException),
            ):
                self._messenger.error_with_icon(
                    f"Error loading configuration: {str(e)}"
                )
            raise
