"""Sync instance command."""

import asyncio

import click

from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)


@click.command()
@click.argument("name")
@click.option("--no-restart", is_flag=True, help="Skip restarting services after sync")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def sync(name: str, no_restart: bool, config: str):
    """Sync instance repositories and configuration."""
    composer = InstanceComposer(config)
    config_data = composer.get_configuration()

    async def _sync():
        use_case = composer.get_sync_instance_use_case()
        await use_case.execute(name, config_data, restart_services=not no_restart)

    try:
        asyncio.run(_sync())
        click.echo(f"Instance '{name}' synchronized successfully")

    except InstanceNotFoundException as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise click.Abort() from e
    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to sync instance: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e
