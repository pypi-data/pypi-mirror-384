"""Rebuild workflow command."""

import click

from dooservice.domains.cloudflare.infrastructure.driving_adapter.cli.cloudflare_cli import (  # noqa: E501
    domain_sync,
)
from dooservice.instance.infrastructure.driving_adapter.cli.commands.base import (
    start,
    stop,
    sync,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)
from dooservice.instance.infrastructure.driving_adapter.cli.helpers import (
    select_instance,
)
from dooservice.shared.messaging.click_messenger import ClickMessenger


@click.command(name="rebuild")
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def rebuild(name: str | None, config: str):
    """
    Rebuild instance: stop + sync + domain sync + start.

    Useful for updating repositories and restarting services.
    Syncs domain configuration if configured.
    """
    # Find domain for this instance
    instance_composer = InstanceComposer(config)
    config_data = instance_composer.get_configuration()

    # Interactive selection if name not provided
    if not name:
        name = select_instance(config_data, "Select instance to rebuild")

    messenger = ClickMessenger()
    messenger.info_with_icon(f"Rebuilding instance '{name}'...")

    try:
        click.echo("  [1/4] Stopping...")
        ctx = click.get_current_context()
        ctx.invoke(stop, name=name, config=config)

        click.echo("  [2/4] Synchronizing repositories...")
        ctx.invoke(sync, name=name, config=config, no_restart=True)

        instance_domain = None
        for domain_name, domain_config in config_data.domains.base_domains.items():
            if domain_config.instance == name:
                instance_domain = domain_name
                break

        # Step 3: Sync domain if configured
        if instance_domain:
            click.echo(f"  [3/4] Synchronizing domain '{instance_domain}'...")
            try:
                ctx.invoke(domain_sync, name=instance_domain, config=config)
                messenger.send_success(f"Domain '{instance_domain}' synchronized")
            except Exception as e:  # noqa: BLE001
                messenger.send_warning(f"Domain sync failed: {str(e)}")
        else:
            click.echo("  [3/4] Skipping domain sync (not configured)")

        click.echo("  [4/4] Starting...")
        ctx.invoke(start, name=name, config=config)

        messenger.success_with_icon(f"Instance '{name}' rebuilt successfully!")
    except click.Abort:
        messenger.error_with_icon("Rebuild failed")
        raise
    except Exception as e:
        messenger.error_with_icon(f"Rebuild failed: {str(e)}")
        raise click.Abort() from e
