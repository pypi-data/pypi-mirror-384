"""Stop instance alias command (down)."""

import click

from dooservice.instance.infrastructure.driving_adapter.cli.commands.base import (
    stop,
)


@click.command(name="down")
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def down_cmd(name: str | None, config: str):
    """Stop instance (alias for 'stop')."""
    ctx = click.get_current_context()
    ctx.invoke(stop, name=name, config=config)
