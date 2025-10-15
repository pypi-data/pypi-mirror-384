"""Update Odoo modules command."""

import asyncio

import click

from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)


@click.command(name="update-modules")
@click.argument("name")
@click.option(
    "--database", "-d", required=True, help="Name of the Odoo database to update"
)
@click.option(
    "--modules",
    "-m",
    multiple=True,
    help="Module names to update (can be specified multiple times)",
)
@click.option(
    "--all",
    "-a",
    "update_all",
    is_flag=True,
    help="Update all modules (equivalent to -u all)",
)
@click.option(
    "--http-port",
    "-p",
    default=9090,
    help="HTTP port to use (default 9090 to avoid conflicts)",
)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def update_modules(
    name: str,
    database: str,
    modules: tuple,
    update_all: bool,
    http_port: int,
    config: str,
):
    """
    Update Odoo modules in an instance.

    This command executes the Odoo update command inside the instance container:
    odoo -c /etc/odoo/odoo.conf -d DATABASE -u MODULES
         --stop-after-init --http-port PORT

    Examples:
    # Update specific modules
    dooservice instance update-modules myinstance -d mydb -m sale -m purchase

    # Update all modules
    dooservice instance update-modules myinstance -d mydb --all
    """
    composer = InstanceComposer(config)

    # Validate that either modules or update_all is specified
    if not modules and not update_all:
        click.echo(
            click.style(
                "Error: Either specify modules with -m/--modules or use --all flag",
                fg="red",
            ),
            err=True,
        )
        raise click.Abort()

    try:
        use_case = composer.update_odoo_modules_use_case
        result = asyncio.run(
            use_case.execute(
                instance_name=name,
                database=database,
                modules=list(modules) if modules else None,
                update_all=update_all,
                http_port=http_port,
            )
        )

        # Show the command output
        if result:
            click.echo("\n--- Odoo Update Output ---")
            click.echo(result)

    except InstanceNotFoundException as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise click.Abort() from e
    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to update modules: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e
