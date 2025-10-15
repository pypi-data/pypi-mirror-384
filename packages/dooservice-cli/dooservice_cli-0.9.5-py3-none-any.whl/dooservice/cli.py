"""
This module serves as the main entry point for the DooService CLI.

It uses the 'click' library to create a group of commands, aggregating them
from the different modules of the application. Each module now has its own
organized CLI structure in driving_adapters/cli.
"""

import click

from dooservice.backup.infrastructure.driving_adapter.cli.backup_cli import backup_cli
from dooservice.core.infrastructure.driving_adapter.cli.main import (
    config_main as core_group,
)
from dooservice.domains.cloudflare.infrastructure.driving_adapter.cli.main import (
    cloudflare_main as cloudflare_group,
)
from dooservice.instance.infrastructure.driving_adapter.cli.main import (
    instance_main as instance_group,
)
from dooservice.repository.infrastructure.driving_adapter.cli.main import (
    repository_main as repository_group,
)


@click.group()
def cli():
    """
    DooService CLI: A tool for managing complex Odoo instances declaratively.

    This CLI allows you to define your instances, repositories, and deployment
    configurations in a single `dooservice.yml` file and manage them from
    the terminal.

    All commands now support the --config/-c option for custom configuration files.
    """


cli.add_command(core_group)
cli.add_command(instance_group)
cli.add_command(repository_group)
cli.add_command(backup_cli)
cli.add_command(cloudflare_group)

if __name__ == "__main__":
    cli()
