from abc import ABC, abstractmethod
from pathlib import Path

from dooservice.core.domain.entities.configuration import DooServiceConfiguration


class ConfigurationRepository(ABC):
    @abstractmethod
    def load_from_file(self, file_path: Path) -> DooServiceConfiguration:
        raise NotImplementedError()

    @abstractmethod
    def save_to_file(
        self, configuration: DooServiceConfiguration, file_path: Path
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def validate_configuration(self, configuration: DooServiceConfiguration) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def parse_yaml_content(self, yaml_content: str) -> DooServiceConfiguration:
        raise NotImplementedError()

    @abstractmethod
    def serialize_to_yaml(self, configuration: DooServiceConfiguration) -> str:
        raise NotImplementedError()
