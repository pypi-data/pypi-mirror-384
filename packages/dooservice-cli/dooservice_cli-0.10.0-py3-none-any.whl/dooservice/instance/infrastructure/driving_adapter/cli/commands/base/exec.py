"""Exec instance command."""

import asyncio
from typing import Optional

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
@click.argument("command")
@click.option("--user", help="User to run the command as")
@click.option("--workdir", help="Working directory for the command")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def exec_cmd(
    name: str, command: str, user: Optional[str], workdir: Optional[str], config: str
):
    """Execute a command inside an instance container."""
    composer = InstanceComposer(config)

    try:
        use_case = composer.exec_instance_use_case
        # Parse command string into list of arguments
        command_args = command.split() if isinstance(command, str) else command
        result = asyncio.run(
            use_case.execute(name, command_args, user=user, workdir=workdir)
        )

        # Show the command output
        if result:
            click.echo(result)

    except InstanceNotFoundException as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise click.Abort() from e
    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to execute command: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e
