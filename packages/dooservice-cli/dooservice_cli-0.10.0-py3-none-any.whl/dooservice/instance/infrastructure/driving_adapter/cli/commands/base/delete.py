"""Delete instance command."""

import asyncio

import click

from dooservice.domains.cloudflare.infrastructure.driving_adapter.cli.cloudflare_cli import (  # noqa: E501
    domain_disable,
)
from dooservice.instance.domain.exceptions.instance_exceptions import (
    InstanceNotFoundException,
    InstanceOperationException,
)
from dooservice.instance.infrastructure.driving_adapter.cli.composer import (
    InstanceComposer,
)
from dooservice.instance.infrastructure.driving_adapter.cli.helpers import (
    select_instance,
)
from dooservice.shared.messaging.click_messenger import ClickMessenger


@click.command()
@click.argument("name", required=False)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option(
    "--force", is_flag=True, help="Force deletion even if directories contain data"
)
def delete(name: str | None, config: str, force: bool):
    """Delete an instance completely."""
    composer = InstanceComposer(config)
    config_data = composer.get_configuration()
    messenger = ClickMessenger()

    # Interactive selection if name not provided
    if not name:
        name = select_instance(config_data, "Select instance to delete")

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

    # Disable domain if configured
    instance_domain = None
    for domain_name, domain_config in config_data.domains.base_domains.items():
        if domain_config.instance == name:
            instance_domain = domain_name
            break

    if instance_domain:
        click.echo(f"Disabling domain '{instance_domain}'...")
        try:
            ctx = click.get_current_context()
            ctx.invoke(domain_disable, name=instance_domain, config=config)
            messenger.send_success(f"Domain '{instance_domain}' disabled")
        except Exception as e:  # noqa: BLE001
            messenger.send_warning(f"Failed to disable domain: {str(e)}")

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
