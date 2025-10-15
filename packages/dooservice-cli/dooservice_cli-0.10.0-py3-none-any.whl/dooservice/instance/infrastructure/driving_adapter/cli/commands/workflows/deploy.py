"""Deploy workflow command."""

import click

from dooservice.domains.cloudflare.infrastructure.driving_adapter.cli.cloudflare_cli import (  # noqa: E501
    domain_enable,
    tunnel_init,
    tunnel_status,
)
from dooservice.instance.infrastructure.driving_adapter.cli.commands.base import (
    create,
    start,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)
from dooservice.instance.infrastructure.driving_adapter.cli.helpers import (
    select_instance,
)
from dooservice.shared.messaging.click_messenger import ClickMessenger


@click.command(name="deploy")
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def deploy(name: str | None, config: str):
    """
    Deploy instance: create + start + domain setup.

    Complete deployment workflow:
    1. Create instance containers
    2. Start all services
    3. Initialize tunnel (if domain configured and tunnel doesn't exist)
    4. Enable domain (if configured)
    """
    # Check if instance has domain configured
    instance_composer = InstanceComposer(config)
    config_data = instance_composer.get_configuration()

    # Interactive selection if name not provided
    if not name:
        name = select_instance(config_data, "Select instance to deploy")

    messenger = ClickMessenger()
    messenger.info_with_icon(f"Deploying instance '{name}'...")

    try:
        click.echo("  [1/4] Creating instance...")
        ctx = click.get_current_context()
        ctx.invoke(create, name=name, config=config)

        click.echo("  [2/4] Starting instance...")
        ctx.invoke(start, name=name, config=config)

        # Find domain for this instance
        instance_domain = None
        for domain_name, domain_config in config_data.domains.base_domains.items():
            if domain_config.instance == name:
                instance_domain = domain_name
                break

        # Setup domain if configured
        if instance_domain and config_data.domains.cloudflare:
            click.echo("  [3/4] Setting up tunnel...")

            # Check if tunnel exists using tunnel status command
            try:
                ctx.invoke(tunnel_status, config=config)
                messenger.send_success("Tunnel already running")
            except Exception:  # noqa: BLE001
                # Tunnel doesn't exist, create it
                try:
                    ctx.invoke(tunnel_init, config=config)
                    messenger.send_success("Tunnel created")
                except Exception as e:  # noqa: BLE001
                    messenger.send_warning(f"Tunnel setup failed: {str(e)}")

            # Enable domain
            click.echo(f"  [4/4] Enabling domain '{instance_domain}'...")
            try:
                ctx.invoke(domain_enable, name=instance_domain, config=config)
                messenger.send_success(f"Domain '{instance_domain}' enabled")
            except Exception as e:  # noqa: BLE001
                messenger.send_warning(f"Domain setup failed: {str(e)}")
        else:
            click.echo("  [3-4/4] Skipping domain setup (not configured)")

        messenger.success_with_icon(f"Instance '{name}' deployed successfully!")

    except click.Abort:
        messenger.error_with_icon("Deployment failed")
        raise
    except Exception as e:
        messenger.error_with_icon(f"Deployment failed: {str(e)}")
        raise click.Abort() from e
