from typing import Any

import click

from .messaging import MessageInterface, MessageLevel


class ClickMessenger(MessageInterface):
    def __init__(self):
        self._level_colors = {
            MessageLevel.DEBUG: "bright_black",
            MessageLevel.INFO: "blue",
            MessageLevel.WARNING: "yellow",
            MessageLevel.ERROR: "red",
            MessageLevel.SUCCESS: "green",
        }

    def send_message(
        self, message: str, level: MessageLevel = MessageLevel.INFO, **kwargs: Any
    ) -> None:
        color = self._level_colors.get(level, "white")
        prefix = f"[{level.value.upper()}]"

        if level == MessageLevel.ERROR:
            click.echo(
                click.style(f"{prefix} {message}", fg=color, bold=True), err=True
            )
        else:
            click.echo(click.style(f"{prefix} {message}", fg=color))

    def send_debug(self, message: str, **kwargs: Any) -> None:
        self.send_message(message, MessageLevel.DEBUG, **kwargs)

    def send_info(self, message: str, **kwargs: Any) -> None:
        self.send_message(message, MessageLevel.INFO, **kwargs)

    def send_warning(self, message: str, **kwargs: Any) -> None:
        self.send_message(message, MessageLevel.WARNING, **kwargs)

    def send_error(self, message: str, **kwargs: Any) -> None:
        self.send_message(message, MessageLevel.ERROR, **kwargs)

    def send_success(self, message: str, **kwargs: Any) -> None:
        self.send_message(message, MessageLevel.SUCCESS, **kwargs)
