import click

from dooservice.repository.infrastructure.driving_adapter.cli.repository_cli import (
    repo_cli,
)


@click.group(name="repository")
def repository_main():
    """Repository management commands."""


# Add the commands directly instead of the group
for command in repo_cli.commands.values():
    repository_main.add_command(command)
