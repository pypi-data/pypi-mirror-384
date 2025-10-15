"""Destroy workflow command."""

import click

from dooservice.instance.infrastructure.driving_adapter.cli.commands.base import (
    delete,
    stop,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)
from dooservice.instance.infrastructure.driving_adapter.cli.helpers import (
    select_instance,
)
from dooservice.shared.messaging.click_messenger import ClickMessenger


@click.command(name="destroy")
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--force", is_flag=True, help="No confirmation prompt")
def destroy(name: str | None, config: str, force: bool):
    """
    Destroy instance completely: stop + delete.

    This is a forceful command that:
    1. Stops instance
    2. Deletes instance (which also disables domain if configured)
    """
    instance_composer = InstanceComposer(config)
    config_data = instance_composer.get_configuration()

    # Interactive selection if name not provided
    if not name:
        name = select_instance(config_data, "Select instance to destroy")

    messenger = ClickMessenger()

    if not force and not click.confirm(
        f"Are you sure you want to destroy instance '{name}'? This cannot be undone.",
        default=False,
    ):
        click.echo("Destruction cancelled")
        return

    messenger.warning_with_icon(f"Destroying instance '{name}'...")

    try:
        ctx = click.get_current_context()

        # Step 1: Stop (ignore errors if already stopped)
        click.echo("  [1/2] Stopping...")
        try:  # noqa: SIM105
            ctx.invoke(stop, name=name, config=config)
        except click.Abort:
            pass

        # Step 2: Delete (which also disables domain if configured)
        click.echo("  [2/2] Deleting...")
        ctx.invoke(delete, name=name, config=config, force=True)

        messenger.success_with_icon(f"Instance '{name}' destroyed successfully!")

    except click.Abort:
        messenger.error_with_icon("Destruction failed")
        raise
    except Exception as e:
        messenger.error_with_icon(f"Destruction failed: {str(e)}")
        raise click.Abort() from e
