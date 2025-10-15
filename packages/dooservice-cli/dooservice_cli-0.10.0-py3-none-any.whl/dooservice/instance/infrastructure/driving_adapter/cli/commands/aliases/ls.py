"""List instances alias command (ls)."""

import click

from dooservice.instance.infrastructure.driving_adapter.cli.commands.base import (
    list_cmd,
)


@click.command(name="ls")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def ls_cmd(config: str):
    """List all instances (alias for 'list')."""
    ctx = click.get_current_context()
    ctx.invoke(list_cmd, config=config)
