# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""
Backup CLI main orchestrator.

Following hexagonal architecture, this is the public interface of the
backup CLI driving adapter.
"""

import click

from dooservice.backup.infrastructure.driving_adapter.cli.backup_cli import backup_cli


@click.group(name="backup")
def backup_main():
    """Backup management commands."""


# Register all backup commands
for command in backup_cli.commands.values():
    backup_main.add_command(command)
