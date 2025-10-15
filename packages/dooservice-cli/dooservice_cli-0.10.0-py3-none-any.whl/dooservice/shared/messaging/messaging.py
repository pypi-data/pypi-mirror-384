from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class MessageLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class MessageInterface(ABC):
    @abstractmethod
    def send_message(
        self, message: str, level: MessageLevel = MessageLevel.INFO, **kwargs: Any
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def send_debug(self, message: str, **kwargs: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def send_info(self, message: str, **kwargs: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def send_warning(self, message: str, **kwargs: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def send_error(self, message: str, **kwargs: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def send_success(self, message: str, **kwargs: Any) -> None:
        raise NotImplementedError()
