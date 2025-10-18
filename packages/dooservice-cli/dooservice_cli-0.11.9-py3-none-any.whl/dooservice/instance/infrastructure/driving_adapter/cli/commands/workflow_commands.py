# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""Workflow instance commands."""

import click

from dooservice.domains.cloudflare.infrastructure.driving_adapter.cli.cloudflare_cli import (  # noqa: E501
    domain_enable,
    domain_sync,
    tunnel_init,
    tunnel_status,
)
from dooservice.instance.infrastructure.driving_adapter.cli.commands.base_commands import (  # noqa: E501
    create,
    delete,
    start,
    stop,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)
from dooservice.shared.cli_components import select_instance
from dooservice.shared.messaging.click_messenger import ClickMessenger

# ============================================================================
# DEPLOY COMMAND
# ============================================================================


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


# ============================================================================
# DESTROY COMMAND
# ============================================================================


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


# ============================================================================
# REBUILD COMMAND
# ============================================================================


@click.command(name="rebuild")
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def rebuild(name: str | None, config: str):
    """
    Rebuild instance: stop + delete (keeping data & domain) + create + start.

    Useful for recreating containers while preserving data and domain.
    Data directories and domain configuration are kept intact during rebuild.
    The domain remains connected and active throughout the process.
    Instance is left running after rebuild completes.
    """
    instance_composer = InstanceComposer(config)
    config_data = instance_composer.get_configuration()

    # Interactive selection if name not provided
    if not name:
        name = select_instance(config_data, "Select instance to rebuild")

    messenger = ClickMessenger()
    messenger.info_with_icon(f"Rebuilding instance '{name}'...")

    try:
        ctx = click.get_current_context()

        # Step 1: Stop
        click.echo("  [1/3] Stopping...")
        try:  # noqa: SIM105
            ctx.invoke(stop, name=name, config=config)
        except click.Abort:
            pass  # Continue even if already stopped

        # Step 2: Delete (keeping data and domain)
        click.echo("  [2/5] Removing containers (keeping data)...")
        ctx.invoke(
            delete,
            name=name,
            config=config,
            force=True,
            keep_data=True,
            keep_domain=True,
        )

        # Step 3: Create
        click.echo("  [3/5] Creating instance...")
        ctx.invoke(create, name=name, config=config)

        # Step 4: Sync domain if configured
        instance_domain = None
        for domain_name, domain_config in config_data.domains.base_domains.items():
            if domain_config.instance == name:
                instance_domain = domain_name
                break

        if instance_domain:
            click.echo(f"  [4/5] Synchronizing domain '{instance_domain}'...")
            try:
                ctx.invoke(domain_sync, name=instance_domain, config=config)
                messenger.send_success(f"Domain '{instance_domain}' synchronized")
            except Exception as e:  # noqa: BLE001
                messenger.send_warning(f"Domain sync failed: {str(e)}")
        else:
            click.echo("  [4/5] Skipping domain sync (not configured)")

        # Step 5: Start instance
        click.echo("  [5/5] Starting instance...")
        ctx.invoke(start, name=name, config=config)

        messenger.success_with_icon(f"Instance '{name}' rebuilt successfully!")
    except click.Abort:
        messenger.error_with_icon("Rebuild failed")
        raise
    except Exception as e:
        messenger.error_with_icon(f"Rebuild failed: {str(e)}")
        raise click.Abort() from e
