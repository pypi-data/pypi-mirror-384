"""Show instance status alias command (ps)."""

import click

from dooservice.instance.infrastructure.driving_adapter.cli.commands.base import (
    list_cmd,
)


@click.command(name="ps")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def ps_cmd(config: str):
    """Show instance status (alias for 'list')."""
    ctx = click.get_current_context()
    ctx.invoke(list_cmd, config=config)
