"""Start instance alias command (up)."""

import click

from dooservice.instance.infrastructure.driving_adapter.cli.commands.base import (
    start,
)


@click.command(name="up")
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def up_cmd(name: str | None, config: str):
    """Start instance (alias for 'start')."""
    ctx = click.get_current_context()
    ctx.invoke(start, name=name, config=config)
