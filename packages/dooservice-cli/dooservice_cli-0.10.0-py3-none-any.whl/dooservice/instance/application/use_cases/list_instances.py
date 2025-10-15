"""Use case for listing all available instances."""

from enum import Enum
from typing import List, Optional

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.instance.domain.entities.instance_info import (
    InstanceInfo,
    InstanceStatus,
)
from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceOperationException,
)
from dooservice.instance.domain.repositories.instance_repository import (
    InstanceRepository,
)
from dooservice.shared.messaging import MessageInterface


class InstanceFilter(str, Enum):
    """Filter options for listing instances."""

    ALL = "all"
    CREATED = "created"
    NOT_CREATED = "not_created"


class ListInstances:
    """Use case to list all available instances with their status."""

    def __init__(
        self,
        instance_repository: InstanceRepository,
        messenger: MessageInterface,
    ):
        self._instance_repository = instance_repository
        self._messenger = messenger

    async def execute(
        self,
        config: DooServiceConfiguration,
        filter_by: Optional[InstanceFilter] = None,
    ) -> List[InstanceInfo]:
        """
        List all instances defined in the configuration file.

        Args:
            config: DooServiceConfiguration with instances definition
            filter_by: Optional filter to show only created, not_created, or all

        Returns:
            List of InstanceInfo objects with status and configuration details
        """
        try:
            self._messenger.send_info(
                "Retrieving list of instances from configuration..."
            )

            if not config.instances:
                self._messenger.send_warning("No instances defined in configuration")
                return []

            instances = []
            # Iterate over instances defined in YML configuration
            for instance_name, instance_config in config.instances.items():
                # Get instance info (status from Docker if exists)
                instance_info = await self._instance_repository.get_instance_info(
                    instance_name
                )

                # Extract domains from base_domains that belong to this instance
                instance_domains = []
                if config.domains and config.domains.base_domains:
                    for (
                        domain_name,
                        domain_config,
                    ) in config.domains.base_domains.items():
                        # Check if this domain belongs to current instance
                        if (
                            hasattr(domain_config, "instance")
                            and domain_config.instance == instance_name
                        ):
                            instance_domains.append(domain_name)

                # Join multiple domains with comma or use first one
                domain_str = ", ".join(instance_domains) if instance_domains else None

                if instance_info:
                    # Update with config information
                    instance_info.odoo_version = instance_config.odoo_version
                    instance_info.domain = domain_str
                    instances.append(instance_info)
                else:
                    # Instance defined in config but not created yet
                    # Mark with NOT_CREATED status so it's clear it doesn't exist
                    instances.append(
                        InstanceInfo(
                            name=instance_name,
                            status=InstanceStatus.NOT_CREATED,
                            services=[],
                            data_dir=instance_config.data_dir,
                            odoo_version=instance_config.odoo_version,
                            domain=domain_str,
                        )
                    )

            if not instances:
                self._messenger.send_warning("No instances found")
                return []

            # Apply filter if specified
            if filter_by == InstanceFilter.CREATED:
                instances = [
                    inst
                    for inst in instances
                    if inst.status != InstanceStatus.NOT_CREATED
                ]
            elif filter_by == InstanceFilter.NOT_CREATED:
                instances = [
                    inst
                    for inst in instances
                    if inst.status == InstanceStatus.NOT_CREATED
                ]
            # InstanceFilter.ALL or None - no filtering needed

            if not instances:
                filter_msg = f" ({filter_by.value})" if filter_by else ""
                self._messenger.send_warning(f"No instances found{filter_msg}")
                return []

            # Count created vs not created (before filtering)
            created_count = sum(
                1 for inst in instances if inst.status != InstanceStatus.NOT_CREATED
            )
            not_created_count = len(instances) - created_count

            # Build informative message
            if filter_by:
                self._messenger.send_success(
                    f"Found {len(instances)} instance(s) (filter: {filter_by.value})"
                )
            elif created_count > 0 and not_created_count > 0:
                self._messenger.send_success(
                    f"Found {len(instances)} instance(s): "
                    f"{created_count} created, {not_created_count} not created"
                )
            else:
                self._messenger.send_success(f"Found {len(instances)} instance(s)")

            return instances

        except Exception as e:  # noqa: BLE001
            self._messenger.send_error(f"Failed to list instances: {str(e)}")
            raise InstanceOperationException(
                f"Failed to list instances: {str(e)}"
            ) from e
