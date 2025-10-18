# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""Alias instance commands."""

import click

from dooservice.instance.infrastructure.driving_adapter.cli.commands.base_commands import (  # noqa: E501
    delete,
    list_cmd,
    start,
    stop,
)

# ============================================================================
# DOWN COMMAND (alias for stop)
# ============================================================================


@click.command(name="down")
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def down_cmd(name: str | None, config: str):
    """Stop instance (alias for 'stop')."""
    ctx = click.get_current_context()
    ctx.invoke(stop, name=name, config=config)


# ============================================================================
# LS COMMAND (alias for list)
# ============================================================================


@click.command(name="ls")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def ls_cmd(config: str):
    """List all instances (alias for 'list')."""
    ctx = click.get_current_context()
    ctx.invoke(list_cmd, config=config)


# ============================================================================
# PS COMMAND (alias for list/status)
# ============================================================================


@click.command(name="ps")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def ps_cmd(config: str):
    """Show instance status (alias for 'list')."""
    ctx = click.get_current_context()
    ctx.invoke(list_cmd, config=config)


# ============================================================================
# RM COMMAND (alias for delete)
# ============================================================================


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


# ============================================================================
# UP COMMAND (alias for start)
# ============================================================================


@click.command(name="up")
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def up_cmd(name: str | None, config: str):
    """Start instance (alias for 'start')."""
    ctx = click.get_current_context()
    ctx.invoke(start, name=name, config=config)
