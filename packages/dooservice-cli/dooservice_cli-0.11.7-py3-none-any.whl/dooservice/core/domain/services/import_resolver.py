"""Service for resolving configuration imports."""

from pathlib import Path
from typing import Any, Dict, List, Set

from dooservice.core.domain.exceptions.configuration_exceptions import (
    ConfigurationParsingException,
)


class ImportResolver:
    """Service for resolving and processing configuration imports."""

    def __init__(self):
        self._visited_files: Set[Path] = set()

    def resolve_imports(
        self,
        config_data: Dict[str, Any],
        base_path: Path,
        yaml_loader_func,
    ) -> List[Dict[str, Any]]:
        """Resolve all imports in a configuration file.

        Args:
            config_data: The configuration dictionary
            base_path: Base path for resolving relative imports
            yaml_loader_func: Function to load YAML files

        Returns:
            List of configuration dictionaries in order (imports first, then main)

        Raises:
            ConfigurationParsingException: If circular import detected
        """
        configs = []

        # Get imports list
        imports = config_data.get("imports", [])
        if not isinstance(imports, list):
            raise ConfigurationParsingException(
                f"'imports' must be a list, got {type(imports).__name__}"
            )

        # Process each import
        for import_path in imports:
            configs.extend(
                self._resolve_import(import_path, base_path, yaml_loader_func)
            )

        # Add main configuration (without imports key)
        main_config = {k: v for k, v in config_data.items() if k != "imports"}
        configs.append(main_config)

        return configs

    def _resolve_import(
        self,
        import_path: str,
        base_path: Path,
        yaml_loader_func,
    ) -> List[Dict[str, Any]]:
        """Resolve a single import path.

        Args:
            import_path: Path to import file
            base_path: Base path for resolving relative paths
            yaml_loader_func: Function to load YAML files

        Returns:
            List of configuration dictionaries

        Raises:
            ConfigurationParsingException: If circular import or file not found
        """
        # Resolve path relative to base
        if Path(import_path).is_absolute():
            resolved_path = Path(import_path)
        else:
            resolved_path = (base_path / import_path).resolve()

        # Check for circular imports
        if resolved_path in self._visited_files:
            raise ConfigurationParsingException(
                f"Circular import detected: {resolved_path}"
            )

        # Check if file exists
        if not resolved_path.exists():
            raise ConfigurationParsingException(
                f"Import file not found: {resolved_path}"
            )

        # Mark as visited
        self._visited_files.add(resolved_path)

        # Load the imported file
        try:
            imported_data = yaml_loader_func(resolved_path)
        except Exception as e:
            raise ConfigurationParsingException(
                f"Error loading import '{resolved_path}': {str(e)}"
            ) from e

        # Recursively resolve imports in the imported file
        return self.resolve_imports(
            imported_data,
            resolved_path.parent,
            yaml_loader_func,
        )

    def reset(self):
        """Reset the visited files set for new import resolution."""
        self._visited_files.clear()
