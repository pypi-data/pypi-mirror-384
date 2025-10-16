"""
Instance validation domain service.

This service provides validation rules for instance operations,
ensuring business invariants are maintained.
"""

from typing import List

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
)


class InstanceValidator:
    """Domain service for validating instance business rules."""

    @staticmethod
    def validate_instance_exists(
        instance_name: str, config: DooServiceConfiguration
    ) -> None:
        """
        Validate that an instance exists in the configuration.

        This is a critical domain invariant that must be checked before
        any operation on an instance to prevent accidental operations
        on wrong containers.

        Args:
            instance_name: Name of the instance to validate
            config: DooServiceConfiguration containing all instances

        Raises:
            InstanceNotFoundException: If instance not found in configuration

        Example:
            >>> validator = InstanceValidator()
            >>> validator.validate_instance_exists("myinstance", config)
        """
        if not config.instances or instance_name not in config.instances:
            available = list(config.instances.keys()) if config.instances else []
            available_str = ", ".join(available) if available else "none"
            raise InstanceNotFoundException(
                instance_name=instance_name,
                message=f"Instance '{instance_name}' not found in configuration. "
                f"Available instances: {available_str}",
            )

    @staticmethod
    def get_available_instances(
        config: DooServiceConfiguration,
    ) -> List[str]:
        """
        Get list of available instance names from configuration.

        Args:
            config: DooServiceConfiguration containing all instances

        Returns:
            List of instance names
        """
        if not config.instances:
            return []
        return list(config.instances.keys())
