"""Create instance command."""

import asyncio

import click

from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceAlreadyExistsException,
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
def create(name: str, config: str):
    """Create a new instance."""

    async def _create():
        composer = InstanceComposer(config)
        config_data = composer.get_configuration()
        use_case = composer.get_create_instance_use_case()
        await use_case.execute(name, config_data)

    try:
        asyncio.run(_create())

    except InstanceAlreadyExistsException as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to create instance: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e
