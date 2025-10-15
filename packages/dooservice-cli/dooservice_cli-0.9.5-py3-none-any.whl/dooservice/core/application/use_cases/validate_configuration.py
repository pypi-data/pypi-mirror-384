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
        self._messenger.send_info("Validating configuration...")

        is_valid = self._validator.validate(configuration)

        if is_valid:
            self._messenger.send_success("Configuration is valid")
        else:
            errors = self._validator.get_validation_errors()
            self._messenger.send_error(
                f"Configuration validation failed with {len(errors)} error(s):"
            )
            for error in errors:
                self._messenger.send_error(f"  - {error}")

        return is_valid
