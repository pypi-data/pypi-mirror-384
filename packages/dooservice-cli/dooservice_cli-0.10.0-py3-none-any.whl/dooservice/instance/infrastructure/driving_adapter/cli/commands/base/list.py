"""List instances command."""

import asyncio

import click

from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceOperationException,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)


def _display_instances_table(instances):
    """Display instances in a simple table format."""
    if not instances:
        click.echo("No instances found in configuration")
        return

    # Header
    click.echo("\nAvailable Instances:")
    click.echo("=" * 80)
    click.echo(
        f"{'Name':<20} {'Status':<15} {'Version':<15} {'Domain':<20} {'Services':<10}"
    )
    click.echo("-" * 80)

    # Rows
    for instance in instances:
        # Format status with color
        status = instance.status.value
        status_colors = {
            "running": "green",
            "stopped": "red",
            "partial": "yellow",
            "error": "red",
            "unknown": "white",
            "not_created": "white",
        }
        color = status_colors.get(status.lower(), "white")
        status_display = click.style(f"● {status}", fg=color)

        # Version
        version = (
            instance.odoo_version
            if instance.odoo_version and instance.odoo_version != "Unknown"
            else "-"
        )

        # Domain
        domain = instance.domain if instance.domain else "-"

        # Services count
        services_count = f"{len(instance.services)}" if instance.services else "0"

        click.echo(
            f"{instance.name:<20} {status_display:<24} {version:<15} "
            f"{domain:<20} {services_count:<10}"
        )

    click.echo("=" * 80)


@click.command()
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def list_cmd(config: str):
    """List all available instances."""
    composer = InstanceComposer(config)

    try:
        # Load configuration from YML file
        config_data = composer.get_configuration()
        use_case = composer.list_instances_use_case
        instances = asyncio.run(use_case.execute(config_data))

        _display_instances_table(instances)

    except InstanceOperationException as e:
        click.echo(click.style(f"Operation error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(
            click.style(f"Failed to list instances: {str(e)}", fg="red"), err=True
        )
        raise click.Abort() from e
