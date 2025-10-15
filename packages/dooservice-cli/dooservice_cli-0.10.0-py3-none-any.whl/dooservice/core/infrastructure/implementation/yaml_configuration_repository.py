from pathlib import Path

from dooservice.core.domain.entities.configuration import DooServiceConfiguration
from dooservice.core.domain.exceptions.configuration_exceptions import (
    ConfigurationFileNotFoundException,
    ConfigurationParsingException,
)
from dooservice.core.domain.repositories.configuration_repository import (
    ConfigurationRepository,
)
from dooservice.core.domain.services.configuration_merger import ConfigurationMerger
from dooservice.core.domain.services.import_resolver import ImportResolver
from dooservice.core.domain.services.parameter_resolution_service import (
    ParameterResolutionService,
)
from dooservice.core.infrastructure.driven_adapter.configuration_mapper import (
    ConfigurationMapper,
)
from dooservice.core.infrastructure.driven_adapter.yaml_parser import YamlParser


class YamlConfigurationRepository(ConfigurationRepository):
    def __init__(self):
        self._parser = YamlParser()
        self._mapper = ConfigurationMapper()
        self._parameter_resolver = ParameterResolutionService()
        self._import_resolver = ImportResolver()
        self._config_merger = ConfigurationMerger()

    def load_from_file(self, file_path: Path) -> DooServiceConfiguration:
        if not file_path.exists():
            raise ConfigurationFileNotFoundException(str(file_path))

        try:
            # Reset import resolver for new file
            self._import_resolver.reset()

            # Resolve to absolute path for consistent import resolution
            absolute_file_path = file_path.resolve()

            # Load main configuration file
            yaml_data = self._parser.load_from_file(absolute_file_path)

            # Resolve imports if present
            if "imports" in yaml_data:
                config_list = self._import_resolver.resolve_imports(
                    yaml_data,
                    absolute_file_path.parent,
                    self._parser.load_from_file,
                )
                # Merge all configurations
                yaml_data = self._config_merger.merge_multiple(config_list)

            # Resolve parameters for each instance
            resolved_yaml_data = self._resolve_configuration_parameters(yaml_data)

            return self._mapper.map_from_dict(resolved_yaml_data)

        except Exception as e:
            if isinstance(e, ConfigurationFileNotFoundException):
                raise
            raise ConfigurationParsingException(str(e), str(file_path)) from e

    def save_to_file(
        self, configuration: DooServiceConfiguration, file_path: Path
    ) -> None:
        try:
            yaml_content = self.serialize_to_yaml(configuration)

            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(yaml_content)

        except OSError as e:
            raise ConfigurationParsingException(
                f"Error saving configuration: {str(e)}", str(file_path)
            ) from e

    def validate_configuration(self, configuration: DooServiceConfiguration) -> bool:
        return True

    def parse_yaml_content(self, yaml_content: str) -> DooServiceConfiguration:
        try:
            yaml_data = self._parser.parse_yaml_content(yaml_content)

            # Note: Imports are not supported when parsing from content string
            # They only work when loading from a file with a base path

            # Resolve parameters for each instance
            resolved_yaml_data = self._resolve_configuration_parameters(yaml_data)

            return self._mapper.map_from_dict(resolved_yaml_data)

        except (ValueError, TypeError) as e:
            raise ConfigurationParsingException(
                f"Error parsing YAML content: {str(e)}"
            ) from e

    def serialize_to_yaml(self, configuration: DooServiceConfiguration) -> str:
        try:
            return self._parser.serialize_to_yaml(configuration)

        except (ValueError, TypeError) as e:
            raise ConfigurationParsingException(
                f"Error serializing configuration to YAML: {str(e)}"
            ) from e

    def _resolve_configuration_parameters(self, yaml_data: dict) -> dict:
        """
        Resolve all parameter references in the configuration data.

        Args:
            yaml_data: The raw YAML data dictionary

        Returns:
            Configuration data with all parameters resolved
        """
        # Make a deep copy to avoid modifying the original data
        import copy

        resolved_data = copy.deepcopy(yaml_data)

        # Apply defaults to instances first (before parameter resolution)
        defaults = resolved_data.get("defaults", {})
        instance_defaults = defaults.get("instance", {})

        if instance_defaults:
            instances = resolved_data.get("instances", {})
            # Apply defaults to each instance (instance config overrides defaults)
            resolved_data["instances"] = (
                self._config_merger.apply_defaults_to_instances(
                    instances, instance_defaults
                )
            )

        # Resolve parameters for each instance
        instances = resolved_data.get("instances", {})
        for instance_name, instance_data in instances.items():
            # Resolve parameters for this instance
            resolved_instance_data = (
                self._parameter_resolver.resolve_instance_parameters(
                    instance_name=instance_name,
                    instance_data=instance_data,
                    global_config=resolved_data,
                )
            )

            # Update the instance data with resolved values
            instances[instance_name] = resolved_instance_data

        return resolved_data
