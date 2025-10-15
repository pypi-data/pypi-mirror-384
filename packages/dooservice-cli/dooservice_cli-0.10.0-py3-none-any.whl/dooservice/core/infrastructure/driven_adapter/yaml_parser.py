from dataclasses import asdict
import os
from pathlib import Path
import re
from typing import Any, Dict

import yaml

from dooservice.core.domain.entities.configuration import DooServiceConfiguration


class YamlParser:
    def __init__(self):
        self._env_var_pattern = re.compile(r"\$\{env_vars\.([^}]+)\}")
        self._var_pattern = re.compile(r"\$\{([^}]+)\}")

    def load_from_file(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path, encoding="utf-8") as file:
            content = file.read()

        return yaml.safe_load(content)

    def save_to_file(self, data: Dict[str, Any], file_path: Path) -> None:
        with open(file_path, "w", encoding="utf-8") as file:
            yaml.dump(
                data,
                file,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    def parse_yaml_content(self, yaml_content: str) -> Dict[str, Any]:
        return yaml.safe_load(yaml_content)

    def serialize_to_yaml(self, configuration: DooServiceConfiguration) -> str:
        config_dict = asdict(configuration)

        config_dict = self._convert_enums_to_values(config_dict)

        return yaml.dump(
            config_dict, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

    def _convert_enums_to_values(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                key: self._convert_enums_to_values(value) for key, value in data.items()
            }
        if isinstance(data, list):
            return [self._convert_enums_to_values(item) for item in data]
        if hasattr(data, "value"):  # This is an enum
            return data.value
        return data

    def resolve_environment_variables(
        self, data: Dict[str, Any], env_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if env_context is None:
            env_context = {}

        return self._resolve_variables_recursive(data, env_context)

    def _resolve_variables_recursive(
        self, data: Any, env_context: Dict[str, Any]
    ) -> Any:
        if isinstance(data, str):
            return self._resolve_string_variables(data, env_context)
        if isinstance(data, dict):
            return {
                key: self._resolve_variables_recursive(value, env_context)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [
                self._resolve_variables_recursive(item, env_context) for item in data
            ]
        return data

    def _resolve_string_variables(self, text: str, env_context: Dict[str, Any]) -> str:
        def env_replacer(match):
            var_name = match.group(1)
            return str(env_context.get(var_name, os.getenv(var_name, match.group(0))))

        def var_replacer(match):
            var_path = match.group(1)
            return self._resolve_variable_path(var_path, env_context)

        text = self._env_var_pattern.sub(env_replacer, text)

        return self._var_pattern.sub(var_replacer, text)

    def _resolve_variable_path(self, var_path: str, env_context: Dict[str, Any]) -> str:
        if var_path in env_context:
            return str(env_context[var_path])

        path_parts = var_path.split(".")
        current = env_context

        try:
            for part in path_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return f"${{{var_path}}}"

            return str(current)
        except (KeyError, TypeError):
            return f"${{{var_path}}}"
