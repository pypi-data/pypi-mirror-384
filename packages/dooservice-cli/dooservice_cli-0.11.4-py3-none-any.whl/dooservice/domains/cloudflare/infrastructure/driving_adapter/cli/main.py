import click

from dooservice.domains.cloudflare.infrastructure.driving_adapter.cli.cloudflare_cli import (  # noqa: E501
    cloudflare_cli,
)


@click.group(name="cloudflare")
def cloudflare_main():
    """Cloudflare domain and tunnel management."""


# Add the commands directly instead of the group
for command in cloudflare_cli.commands.values():
    cloudflare_main.add_command(command)
