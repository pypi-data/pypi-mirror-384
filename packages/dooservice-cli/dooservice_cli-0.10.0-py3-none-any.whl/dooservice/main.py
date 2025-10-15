"""
DooService CLI entry point.

This orchestrator imports and registers all module CLIs following
hexagonal architecture. Each module exposes its public interface
through its main.py file.
"""

import subprocess
import sys

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
from dooservice.shared.messaging import ClickMessenger


class OrderedGroup(click.Group):
    """Custom Click Group that maintains command order and shows sections."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_sections = {
            "Instance Management": [],
            "Quick Aliases": [],
            "Workflows": [],
            "Infrastructure": [],
            "System": [],
        }

    def add_command(self, cmd, name=None, section="Instance Management"):
        """Add command to a specific section."""
        super().add_command(cmd, name)
        command_name = name or cmd.name
        if section in self.command_sections:
            self.command_sections[section].append(command_name)

    def format_commands(self, ctx, formatter):
        """Format commands with sections."""
        for section, commands in self.command_sections.items():
            if not commands:
                continue

            # Filter to only include registered commands
            section_commands = [
                (cmd, self.commands[cmd]) for cmd in commands if cmd in self.commands
            ]

            if section_commands:
                with formatter.section(f"{section}"):
                    formatter.write_dl(
                        [
                            (cmd, self.commands[cmd].get_short_help_str(limit=60))
                            for cmd, _ in section_commands
                        ]
                    )


@click.group(cls=OrderedGroup)
@click.version_option(version="0.9.5", prog_name="dooservice")
def main():
    r"""DooService CLI.

    \b
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   DooService - Professional Odoo Instance Management        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝

    \b
    Quick Start Examples:
      dooservice create         Create new instance
      dooservice ls             List all instances
      dooservice up             Start instance
      dooservice deploy         Deploy instance (create + start)
      dooservice doctor         Check system health

    Use 'dooservice COMMAND --help' for more information on a command.
    """


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
# NIVEL 3: Global Utilities
# =====================================


@click.command(name="doctor")
def doctor_cmd():
    """Check system dependencies."""
    messenger = ClickMessenger()

    messenger.info_with_icon("DooService System Check")
    click.echo("=" * 50)

    checks = [
        ("Docker", ["docker", "--version"]),
        ("Docker Compose", ["docker", "compose", "version"]),
        ("Git", ["git", "--version"]),
        ("Python", [sys.executable, "--version"]),
    ]

    all_ok = True
    for name, cmd in checks:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=5
            )
            version = result.stdout.strip().split("\n")[0]
            click.echo(click.style(f"✓ {name}: ", fg="green") + version)
        except Exception:  # noqa: BLE001
            click.echo(click.style(f"✗ {name}: Not found", fg="red"))
            all_ok = False

    click.echo("=" * 50)
    if all_ok:
        messenger.success_with_icon("All checks passed!")
    else:
        messenger.error_with_icon("Some dependencies missing")
        sys.exit(1)


# Register doctor command in System section
main.add_command(doctor_cmd, section="System")


if __name__ == "__main__":
    main()
