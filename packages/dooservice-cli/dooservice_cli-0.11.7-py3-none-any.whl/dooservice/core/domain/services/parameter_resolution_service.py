import re
from typing import Any, Dict


class ParameterResolutionService:
    def __init__(self):
        self._var_pattern = re.compile(r"\$\{([^}]+)\}")

    def resolve_instance_parameters(
        self,
        instance_name: str,
        instance_data: Dict[str, Any],
        global_config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Resolve all parameters for a single instance configuration.

        Args:
            instance_name: The name of the instance (used as ${name})
            instance_data: The instance configuration dictionary
            global_config: Global configuration context (optional)

        Returns:
            Instance configuration with all parameters resolved
        """
        if global_config is None:
            global_config = {}

        # Build the resolution context for this instance
        context = self._build_instance_context(
            instance_name, instance_data, global_config
        )

        # Resolve parameters recursively with multiple passes for nested resolution
        return self._resolve_with_multiple_passes(instance_data, context)

    def _build_instance_context(
        self,
        instance_name: str,
        instance_data: Dict[str, Any],
        global_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build the parameter resolution context for an instance."""
        context = {
            "name": instance_name,
            "odoo_version": instance_data.get("odoo_version", "19.0"),
            "db_version": instance_data.get("db_version", "17"),
        }

        # First pass: resolve data_dir which may contain ${name}
        raw_data_dir = instance_data.get("data_dir", f"/opt/odoo-data/{instance_name}")
        resolved_data_dir = self._resolve_string_variables(raw_data_dir, context)
        context["data_dir"] = resolved_data_dir

        # Add paths to context (these may reference ${data_dir})
        if "paths" in instance_data:
            context["paths"] = {}
            for path_key, path_value in instance_data["paths"].items():
                context["paths"][path_key] = self._resolve_string_variables(
                    str(path_value), context
                )

        # Add env_vars to context
        if "env_vars" in instance_data:
            context["env_vars"] = {}
            for env_key, env_value in instance_data["env_vars"].items():
                context["env_vars"][env_key] = self._resolve_string_variables(
                    str(env_value), context
                )

        # Add ports to context
        if "ports" in instance_data:
            context["ports"] = {}
            for port_key, port_value in instance_data["ports"].items():
                context["ports"][port_key] = str(port_value)

        return context

    def _resolve_with_multiple_passes(
        self, data: Any, context: Dict[str, Any], max_passes: int = 3
    ) -> Any:
        """
        Resolve parameters with multiple passes to handle nested references.

        Args:
            data: The data to resolve
            context: The resolution context
            max_passes: Maximum number of resolution passes

        Returns:
            Data with all resolvable parameters resolved
        """
        current_data = data

        for pass_num in range(max_passes):
            resolved_data = self._resolve_variables_recursive(current_data, context)

            # If no changes occurred, we're done
            if resolved_data == current_data:
                break

            current_data = resolved_data

            # Update context with newly resolved values if needed
            if isinstance(resolved_data, dict) and pass_num == 0:
                # After first pass, update context with resolved paths and env_vars
                if "paths" in resolved_data:
                    context["paths"] = resolved_data["paths"]
                if "env_vars" in resolved_data:
                    context["env_vars"] = resolved_data["env_vars"]

        return current_data

    def _resolve_variables_recursive(self, data: Any, context: Dict[str, Any]) -> Any:
        """Recursively resolve variables in data structures."""
        if isinstance(data, str):
            return self._resolve_string_variables(data, context)
        if isinstance(data, dict):
            return {
                key: self._resolve_variables_recursive(value, context)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [self._resolve_variables_recursive(item, context) for item in data]
        return data

    def _resolve_string_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Resolve ${var} patterns in a string."""

        def var_replacer(match):
            var_path = match.group(1)
            return self._resolve_variable_path(var_path, context)

        return self._var_pattern.sub(var_replacer, text)

    def _resolve_variable_path(self, var_path: str, context: Dict[str, Any]) -> str:
        """Resolve a variable path.

        Examples: 'name', 'data_dir', 'paths.config', 'env_vars.DB_HOST', etc.

        Args:
            var_path: The variable path to resolve (e.g., 'name', 'paths.config')
            context: The resolution context

        Returns:
            The resolved value as a string, or the original ${var_path} if not found
        """
        # Handle direct variables
        if var_path in context:
            return str(context[var_path])

        # Handle nested paths like 'paths.config', 'env_vars.DB_HOST'
        path_parts = var_path.split(".")
        current = context

        try:
            for part in path_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    # Variable not found, return original placeholder
                    return f"${{{var_path}}}"

            return str(current)
        except (KeyError, TypeError):
            # Error resolving path, return original placeholder
            return f"${{{var_path}}}"
