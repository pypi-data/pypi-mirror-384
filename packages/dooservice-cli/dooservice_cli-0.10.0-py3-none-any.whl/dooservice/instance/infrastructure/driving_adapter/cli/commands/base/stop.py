"""Stop instance command."""

import asyncio

import click

from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)
from dooservice.instance.infrastructure.driving_adapter.cli.helpers import (
    select_instance,
)


@click.command()
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def stop(name: str | None, config: str):
    """Stop an instance."""
    composer = InstanceComposer(config)
    config_data = composer.get_configuration()

    # Interactive selection if name not provided
    if not name:
        name = select_instance(config_data, "Select instance to stop")

    try:
        use_case = composer.stop_instance_use_case
        asyncio.run(use_case.execute(name))

    except InstanceNotFoundException as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise click.Abort() from e
    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to stop instance: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e
