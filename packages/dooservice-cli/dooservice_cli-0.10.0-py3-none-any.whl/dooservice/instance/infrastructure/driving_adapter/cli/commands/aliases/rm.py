"""Remove instance alias command (rm)."""

import click

from dooservice.instance.infrastructure.driving_adapter.cli.commands.base import (
    delete,
)


@click.command(name="rm")
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--force", is_flag=True, help="Force deletion without confirmation")
def rm_cmd(name: str | None, config: str, force: bool):
    """Remove instance (alias for 'delete')."""
    ctx = click.get_current_context()
    ctx.invoke(delete, name=name, config=config, force=force)
