"""Restart instance command."""

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
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def restart(name: str, config: str):
    """Restart an instance (stop + start)."""
    composer = InstanceComposer(config)

    try:
        use_case = composer.restart_instance_use_case
        asyncio.run(use_case.execute(name))

    except InstanceNotFoundException as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise click.Abort() from e
    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to restart instance: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e
