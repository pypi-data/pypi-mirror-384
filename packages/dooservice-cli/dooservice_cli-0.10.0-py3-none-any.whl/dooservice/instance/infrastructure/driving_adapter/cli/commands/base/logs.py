"""Logs instance command."""

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
@click.option("--service", help="Specific service to get logs from (web, db)")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option(
    "--tail", default=100, help="Number of lines to show from the end of the logs"
)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def logs(name: str, service: Optional[str], follow: bool, tail: int, config: str):
    """Get instance logs."""
    composer = InstanceComposer(config)

    try:
        use_case = composer.logs_instance_use_case
        result = asyncio.run(
            use_case.execute(name, service=service, tail=tail, follow=follow)
        )

        if isinstance(result, str):
            # Static logs
            if result:
                click.echo(result)
        else:
            # Streaming logs (generator)
            try:
                for log_line in result:
                    click.echo(log_line)
            except KeyboardInterrupt:
                click.echo("\nLog streaming interrupted by user")
            except Exception as e:  # noqa: BLE001
                click.echo(
                    click.style(f"Error while streaming logs: {str(e)}", fg="red"),
                    err=True,
                )

    except InstanceNotFoundException as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise click.Abort() from e
    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(click.style(f"Failed to get logs: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
