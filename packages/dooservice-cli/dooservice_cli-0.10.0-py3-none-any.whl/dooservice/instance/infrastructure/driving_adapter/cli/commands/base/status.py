"""Status instance command."""

import asyncio

import click

from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)


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


def _display_status(status_info):
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


@click.command()
@click.argument("name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def status(name: str, config: str):
    """Show instance status."""
    composer = InstanceComposer(config)

    try:
        use_case = composer.status_instance_use_case
        status_info = asyncio.run(use_case.execute(name))
        _display_status(status_info)

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
