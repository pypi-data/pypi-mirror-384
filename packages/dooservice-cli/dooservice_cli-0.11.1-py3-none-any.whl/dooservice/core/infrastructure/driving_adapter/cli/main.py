import click

from dooservice.core.infrastructure.driving_adapter.cli.configuration_cli import (
    config_cli,
)


@click.group(name="config")
def config_main():
    """Core configuration management commands."""


# Add the commands directly instead of the group
for command in config_cli.commands.values():
    config_main.add_command(command)
