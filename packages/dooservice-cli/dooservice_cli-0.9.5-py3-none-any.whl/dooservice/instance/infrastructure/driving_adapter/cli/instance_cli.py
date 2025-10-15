"""
Instance CLI with standardized architecture following core module structure.

This module implements instance CLI commands using the same structure as core and
repository modules,
with proper dependency injection through composer pattern.
"""

import asyncio
from typing import Optional

import click

from dooservice.instance.application.use_cases.list_instances import InstanceFilter
from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceAlreadyExistsException,
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)


def _validate_instance_or_abort(validator, config_data, instance_name: str) -> None:
    """
    Validate instance exists in configuration or abort with error message.

    Args:
        validator: InstanceValidator instance
        config_data: DooServiceConfiguration
        instance_name: Name of instance to validate
    """
    try:
        validator.validate_instance_exists(instance_name, config_data)
    except InstanceNotFoundException as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise click.Abort() from e


@click.group(name="instance")
def instance_cli():
    """Instance management commands."""


@instance_cli.command()
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def list(config: str):
    """List all available instances."""
    composer = InstanceComposer(config)
    presenter = composer.instance_presenter

    try:
        # Load configuration from YML file
        config_data = composer.get_configuration()
        use_case = composer.list_instances_use_case
        instances = asyncio.run(use_case.execute(config_data))

        if instances:
            presenter.display_table(instances)
        else:
            click.echo("No instances found in configuration")

    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to list instances: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e


@instance_cli.command()
@click.argument("name", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Select instance interactively")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def create(name: Optional[str], interactive: bool, config: str):
    """Create a new instance."""
    composer = InstanceComposer(config)
    presenter = composer.instance_presenter

    # Handle interactive mode - show only NOT CREATED instances
    if interactive or not name:
        try:
            config_data = composer.get_configuration()
            list_use_case = composer.list_instances_use_case
            instances = asyncio.run(
                list_use_case.execute(config_data, filter_by=InstanceFilter.NOT_CREATED)
            )
            if not instances:
                presenter.display_no_instances_message("not created")
                return
            name = presenter.select_instance_interactive(instances)
            if not name:
                click.echo("No instance selected")
                return
        except Exception as e:
            click.echo(
                click.style(f"Failed to list instances: {str(e)}", fg="red"), err=True
            )
            raise click.Abort() from e

    async def _create():
        composer = InstanceComposer(config)
        config_data = composer.get_configuration()
        use_case = composer.get_create_instance_use_case()
        await use_case.execute(name, config_data)

    try:
        asyncio.run(_create())
        click.echo(f"Instance '{name}' created successfully")

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


@instance_cli.command()
@click.argument("name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option(
    "--force", is_flag=True, help="Force deletion even if directories contain data"
)
def delete(name: str, config: str, force: bool):
    """Delete an instance completely."""
    composer = InstanceComposer(config)

    # Validate instance exists in YML BEFORE any operation
    config_data = composer.get_configuration()
    _validate_instance_or_abort(composer.instance_validator, config_data, name)

    # Only ask for confirmation if --force is not used
    if not force:
        if not click.confirm(
            f"Are you sure you want to delete instance '{name}'? "
            f"This action cannot be undone."
        ):
            click.echo("Deletion cancelled")
            return

        # User confirmed manually, so we can force directory deletion
        force_directories = True
    else:
        # --force flag was used, force everything
        force_directories = True

    async def _delete():
        use_case = composer.delete_instance_use_case
        await use_case.execute(name, config_data, force=force_directories)

    try:
        asyncio.run(_delete())
        click.echo(f"Instance '{name}' deleted successfully")

    except InstanceNotFoundException as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to delete instance: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e


@instance_cli.command()
@click.argument("name", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Select instance interactively")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def start(name: Optional[str], interactive: bool, config: str):
    """Start an instance."""
    composer = InstanceComposer(config)
    presenter = composer.instance_presenter

    # Handle interactive mode - show only CREATED instances
    if interactive or not name:
        try:
            config_data = composer.get_configuration()
            list_use_case = composer.list_instances_use_case
            instances = asyncio.run(
                list_use_case.execute(config_data, filter_by=InstanceFilter.CREATED)
            )
            if not instances:
                presenter.display_no_instances_message("created")
                return
            name = presenter.select_instance_interactive(instances)
            if not name:
                click.echo("No instance selected")
                return
        except Exception as e:
            click.echo(
                click.style(f"Failed to list instances: {str(e)}", fg="red"), err=True
            )
            raise click.Abort() from e
    else:
        # Validate instance exists in YML BEFORE any operation
        config_data = composer.get_configuration()
        _validate_instance_or_abort(composer.instance_validator, config_data, name)

    try:
        use_case = composer.start_instance_use_case
        asyncio.run(use_case.execute(name))
        click.echo(f"Instance '{name}' started successfully")

    except InstanceNotFoundException as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise click.Abort() from e
    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to start instance: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e


@instance_cli.command()
@click.argument("name", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Select instance interactively")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def stop(name: Optional[str], interactive: bool, config: str):
    """Stop an instance."""
    composer = InstanceComposer(config)
    presenter = composer.instance_presenter

    # Handle interactive mode - show only CREATED instances
    if interactive or not name:
        try:
            config_data = composer.get_configuration()
            list_use_case = composer.list_instances_use_case
            instances = asyncio.run(
                list_use_case.execute(config_data, filter_by=InstanceFilter.CREATED)
            )
            if not instances:
                presenter.display_no_instances_message("created")
                return
            name = presenter.select_instance_interactive(instances)
            if not name:
                click.echo("No instance selected")
                return
        except Exception as e:
            click.echo(
                click.style(f"Failed to list instances: {str(e)}", fg="red"), err=True
            )
            raise click.Abort() from e
    else:
        # Validate instance exists in YML BEFORE any operation
        config_data = composer.get_configuration()
        _validate_instance_or_abort(composer.instance_validator, config_data, name)

    try:
        use_case = composer.stop_instance_use_case
        asyncio.run(use_case.execute(name))
        click.echo(f"Instance '{name}' stopped successfully")

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


@instance_cli.command()
@click.argument("name", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Select instance interactively")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def restart(name: Optional[str], interactive: bool, config: str):
    """Restart an instance (stop + start)."""
    composer = InstanceComposer(config)
    presenter = composer.instance_presenter

    # Handle interactive mode - show only CREATED instances
    if interactive or not name:
        try:
            config_data = composer.get_configuration()
            list_use_case = composer.list_instances_use_case
            instances = asyncio.run(
                list_use_case.execute(config_data, filter_by=InstanceFilter.CREATED)
            )
            if not instances:
                presenter.display_no_instances_message("created")
                return
            name = presenter.select_instance_interactive(instances)
            if not name:
                click.echo("No instance selected")
                return
        except Exception as e:
            click.echo(
                click.style(f"Failed to list instances: {str(e)}", fg="red"), err=True
            )
            raise click.Abort() from e
    else:
        # Validate instance exists in YML BEFORE any operation
        config_data = composer.get_configuration()
        _validate_instance_or_abort(composer.instance_validator, config_data, name)

    try:
        use_case = composer.restart_instance_use_case
        asyncio.run(use_case.execute(name))
        click.echo(f"Instance '{name}' restarted successfully")

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


@instance_cli.command()
@click.argument("name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def status(name: str, config: str):
    """Show instance status."""
    composer = InstanceComposer(config)

    # Validate instance exists in YML BEFORE any operation
    config_data = composer.get_configuration()
    _validate_instance_or_abort(composer.instance_validator, config_data, name)

    try:
        use_case = composer.status_instance_use_case
        status_info = asyncio.run(use_case.execute(name))
        _display_instance_status(status_info)

    except InstanceNotFoundException as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise click.Abort() from e
    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to get instance status: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e


@instance_cli.command()
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

    # Validate instance exists in YML BEFORE any operation
    config_data = composer.get_configuration()
    _validate_instance_or_abort(composer.instance_validator, config_data, name)

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


@instance_cli.command()
@click.argument("name")
@click.argument("command")
@click.option("--user", help="User to run the command as")
@click.option("--workdir", help="Working directory for the command")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def exec(
    name: str, command: str, user: Optional[str], workdir: Optional[str], config: str
):
    """Execute a command inside an instance container."""
    composer = InstanceComposer(config)

    # Validate instance exists in YML BEFORE any operation
    config_data = composer.get_configuration()
    _validate_instance_or_abort(composer.instance_validator, config_data, name)

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


@instance_cli.command()
@click.argument("name")
@click.option("--no-restart", is_flag=True, help="Skip restarting services after sync")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def sync(name: str, no_restart: bool, config: str):
    """Sync instance repositories and configuration."""
    composer = InstanceComposer(config)

    # Validate instance exists in YML BEFORE any operation
    config_data = composer.get_configuration()
    _validate_instance_or_abort(composer.instance_validator, config_data, name)

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


@instance_cli.command(name="update-modules")
@click.argument("name", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Select instance interactively")
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
    name: Optional[str],
    interactive: bool,
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

    # Update all modules with interactive selection
    dooservice instance update-modules -i -d mydb --all

    # Interactive instance selection
    dooservice instance update-modules -i -d mydb -m account -p 9091
    """
    composer = InstanceComposer(config)
    presenter = composer.instance_presenter

    # Handle interactive mode - show only CREATED instances
    if interactive or not name:
        try:
            config_data = composer.get_configuration()
            list_use_case = composer.list_instances_use_case
            instances = asyncio.run(
                list_use_case.execute(config_data, filter_by=InstanceFilter.CREATED)
            )
            if not instances:
                presenter.display_no_instances_message("created")
                return
            name = presenter.select_instance_interactive(instances)
            if not name:
                click.echo("No instance selected")
                return
        except Exception as e:
            click.echo(
                click.style(f"Failed to list instances: {str(e)}", fg="red"), err=True
            )
            raise click.Abort() from e
    else:
        # Validate instance exists in YML BEFORE any operation
        config_data = composer.get_configuration()
        _validate_instance_or_abort(composer.instance_validator, config_data, name)

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


def _display_instance_status(status_info):
    """Display instance status information."""
    if not status_info:
        click.echo("No status information available")
        return

    click.echo(
        f"\nInstance Status: {click.style(status_info.name, fg='cyan', bold=True)}"
    )
    click.echo("=" * 50)

    # Display general status
    state_color = _get_state_color(status_info.status.value)
    click.echo(f"State: {click.style(status_info.status.value, fg=state_color)}")
    click.echo(f"Data Directory: {status_info.data_dir}")
    click.echo(f"Odoo Version: {status_info.odoo_version}")

    if status_info.domain:
        click.echo(f"Domain: {status_info.domain}")

    # Display services information
    if status_info.services:
        click.echo(f"\nServices ({len(status_info.services)}):")
        click.echo("-" * 30)
        for service in status_info.services:
            service_color = _get_state_color(service.status.value)
            click.echo(
                f"  {service.name}: "
                f"{click.style(service.status.value, fg=service_color)}"
            )
            if service.container_id:
                click.echo(f"    Container ID: {service.container_id[:12]}...")
            if service.message:
                click.echo(f"    Message: {service.message}")

    # Health status
    health_text = "Healthy" if status_info.is_healthy() else "Unhealthy"
    health_color = "green" if status_info.is_healthy() else "red"
    click.echo(f"\nHealth: {click.style(health_text, fg=health_color)}")


def _get_state_color(state: str) -> str:
    """Get color for instance/container state."""
    state_colors = {
        "running": "green",
        "stopped": "red",
        "partial": "yellow",
        "error": "red",
        "unknown": "white",
    }
    return state_colors.get(state.lower(), "white")
