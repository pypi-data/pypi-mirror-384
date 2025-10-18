# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""Custom Click Group for ordered command display with sections."""

from importlib.metadata import version
import sys

import click

from dooservice.shared.messaging import ClickMessenger
from dooservice.shared.messaging.constants import (
    DOOSERVICE_LOGO,
    DOOSERVICE_LOGO_MINIMAL,
    Colors,
)


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

    def format_help(self, ctx, formatter):
        """Custom help formatter with ASCII logo."""
        # Print logo without Click formatting it
        click.echo(click.style(DOOSERVICE_LOGO_MINIMAL, fg=Colors.PRIMARY, bold=True))
        click.echo()

        # Quick commands section
        click.echo(click.style("Quick Commands:", fg=Colors.SECONDARY, bold=True))
        click.echo("  dooservice init              Initialize configuration")
        click.echo("  dooservice create <name>     Create new instance")
        click.echo("  dooservice ls                List instances")
        click.echo("  dooservice up                Start instance")
        click.echo("  dooservice deploy <name>     Full deployment")
        click.echo("  dooservice doctor            Check system")
        click.echo("  dooservice --version         Show version")
        click.echo()

        # Format all command sections
        self.format_commands(ctx, formatter)

        # Footer
        click.echo()
        click.echo(click.style("Documentation:", fg=Colors.SECONDARY))
        click.echo("  https://github.com/apiservicesac/dooservice-cli")
        click.echo()

    def format_version(self, ctx, param, value):
        """Custom version formatter with style and animations."""
        if not value or ctx.resilient_parsing:
            return

        messenger = ClickMessenger()

        # Show full ASCII logo
        click.echo()
        click.echo(click.style(DOOSERVICE_LOGO, fg=Colors.PRIMARY, bold=True))
        click.echo()

        # Professional title with colors
        click.echo(
            click.style(
                "Professional Odoo Instance Management",
                fg=Colors.SECONDARY,
                bold=True,
            )
        )
        click.echo()

        # Separator with style
        messenger.draw_section("Version Information", color=Colors.PRIMARY)
        click.echo()

        # Get version dynamically from package metadata
        try:
            package_version = version("dooservice-cli")
        except Exception:  # noqa: BLE001
            package_version = "0.0.0-dev"

        # Version metrics with icons and colors
        messenger.show_metric(
            "Version", package_version, icon="🚀", color=Colors.SUCCESS
        )
        python_version = (
            f"{sys.version_info.major}.{sys.version_info.minor}"
            f".{sys.version_info.micro}"
        )
        messenger.show_metric("Python", python_version, icon="🐍", color=Colors.INFO)
        messenger.show_metric("Platform", sys.platform, icon="💻", color=Colors.INFO)

        click.echo()
        messenger.draw_section("Status", color=Colors.SUCCESS)
        click.echo()

        # Success animation
        messenger.show_success_animation("All systems ready!")
        messenger.show_status_badge("CLI Status", "OPERATIONAL", success=True)

        click.echo()
        click.echo(
            click.style("Documentation: ", fg=Colors.SECONDARY)
            + "https://github.com/apiservicesac/dooservice-cli"
        )
        click.echo()

        ctx.exit()

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
