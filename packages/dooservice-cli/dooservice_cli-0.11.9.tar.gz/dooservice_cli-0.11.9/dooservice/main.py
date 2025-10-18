# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""
DooService CLI entry point.

This orchestrator imports and registers all module CLIs following
hexagonal architecture. Each module exposes its public interface
through its main.py file.
"""

import click

# Import module main orchestrators
from dooservice.backup.infrastructure.driving_adapter.cli.main import backup_main
from dooservice.core.infrastructure.driving_adapter.cli.main import (
    config_main as core_group,
)
from dooservice.domains.cloudflare.infrastructure.driving_adapter.cli.main import (
    cloudflare_main,
)
from dooservice.instance.infrastructure.driving_adapter.cli.main import instance_main
from dooservice.repository.infrastructure.driving_adapter.cli.main import (
    repository_main,
)
from dooservice.shared.cli_components import OrderedGroup, doctor_cmd, init_cmd
from dooservice.shared.messaging.constants import DOOSERVICE_LOGO, Colors

# =====================================
# Main CLI Group
# =====================================


@click.group(cls=OrderedGroup, invoke_without_command=True)
@click.option(
    "--version",
    is_flag=True,
    callback=lambda ctx, param, value: ctx.command.format_version(ctx, param, value),
    expose_value=False,
    is_eager=True,
    help="Show version information",
)
@click.pass_context
def main(ctx):
    """DooService CLI - Professional Odoo Instance Management."""
    # Show welcome screen if no command is provided
    if ctx.invoked_subcommand is None:
        click.echo(click.style(DOOSERVICE_LOGO, fg=Colors.PRIMARY, bold=True))
        click.echo(
            click.style(
                "Professional Odoo Instance Management",
                fg=Colors.SECONDARY,
                bold=True,
            )
        )
        click.echo()
        click.echo("  dooservice create <name>     Create new instance")
        click.echo("  dooservice ls                List instances")
        click.echo("  dooservice up                Start instance")
        click.echo("  dooservice deploy <name>     Full deployment")
        click.echo()
        click.echo("  Use --help for more information")
        click.echo()


# =====================================
# NIVEL 1: Instance Commands (Direct Access)
# =====================================

# Define which commands go in which section
aliases = ["ls", "ps", "rm", "up", "down"]
workflows = ["deploy", "rebuild", "destroy"]
instance_base = [
    "create",
    "delete",
    "start",
    "stop",
    "restart",
    "list",
    "status",
    "logs",
    "exec",
    "sync",
    "update-modules",
]

# Register instance commands at root level with sections
for command_name, command in instance_main.commands.items():
    if command_name in aliases:
        section = "Quick Aliases"
    elif command_name in workflows:
        section = "Workflows"
    else:
        section = "Instance Management"
    main.add_command(command, name=command_name, section=section)


# =====================================
# NIVEL 2: Namespaced Commands
# =====================================


# Extract domain and tunnel subgroups from cloudflare_main
@click.group(name="domain")
def domain_group():
    """Manage domains and DNS."""


@click.group(name="tunnel")
def tunnel_group():
    """Manage Cloudflare tunnels."""


# Register cloudflare subcommands
if "domain" in cloudflare_main.commands:
    for cmd in cloudflare_main.commands["domain"].commands.values():
        domain_group.add_command(cmd)

if "tunnel" in cloudflare_main.commands:
    for cmd in cloudflare_main.commands["tunnel"].commands.values():
        tunnel_group.add_command(cmd)


# Repository module
@click.group(name="repo")
def repo_group():
    """Manage repositories."""


for command in repository_main.commands.values():
    repo_group.add_command(command)


# Backup module
@click.group(name="backup")
def backup_group():
    """Manage backups."""


for command in backup_main.commands.values():
    backup_group.add_command(command)


# Configuration module
@click.group(name="config")
def config_group():
    """Manage configuration."""


for command in core_group.commands.values():
    config_group.add_command(command)

# Add infrastructure groups to main with proper section
main.add_command(domain_group, section="Infrastructure")
main.add_command(tunnel_group, section="Infrastructure")
main.add_command(repo_group, section="Infrastructure")
main.add_command(backup_group, section="Infrastructure")
main.add_command(config_group, section="System")


# =====================================
# NIVEL 3: Register System Commands
# =====================================

# Register system commands in System section
main.add_command(init_cmd, section="System")
main.add_command(doctor_cmd, section="System")


if __name__ == "__main__":
    main()
