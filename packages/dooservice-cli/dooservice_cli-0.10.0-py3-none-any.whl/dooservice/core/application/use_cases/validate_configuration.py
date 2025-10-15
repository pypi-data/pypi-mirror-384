from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.core.domain.services.configuration_validator import (
    ConfigurationValidator,
)
from dooservice.shared.messaging import MessageInterface


class ValidateConfiguration:
    def __init__(self, validator: ConfigurationValidator, messenger: MessageInterface):
        self._validator = validator
        self._messenger = messenger

    def execute(self, configuration: DooServiceConfiguration) -> bool:
        with self._messenger.spinner_context("Validating configuration") as spinner:
            is_valid = self._validator.validate(configuration)

            if is_valid:
                spinner.stop("Configuration is valid", success=True)
            else:
                errors = self._validator.get_validation_errors()
                spinner.stop(
                    f"Configuration validation failed with {len(errors)} error(s)",
                    success=False,
                )
                for error in errors:
                    self._messenger.error_with_icon(f"  {error}")

        return is_valid
