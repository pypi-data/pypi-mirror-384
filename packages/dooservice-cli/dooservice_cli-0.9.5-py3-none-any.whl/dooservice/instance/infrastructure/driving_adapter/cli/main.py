import click

from dooservice.instance.infrastructure.driving_adapter.cli.instance_cli import (
    instance_cli,
)


@click.group(name="instance")
def instance_main():
    """Instance management commands."""


# Add the commands directly instead of the group
for command in instance_cli.commands.values():
    instance_main.add_command(command)
