# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""System commands for DooService CLI."""

from pathlib import Path
import shutil
import subprocess
import sys

import click

from dooservice.shared.messaging import ClickMessenger
from dooservice.shared.messaging.constants import Colors


@click.command(name="doctor")
def doctor_cmd():
    """Check system dependencies and health."""
    messenger = ClickMessenger()

    # Show banner with logo
    click.echo()
    messenger.draw_double_box(
        "DooService System Health Check\nVerifying dependencies and configuration",
        color=Colors.PRIMARY,
    )
    click.echo()

    checks = [
        ("Docker", ["docker", "--version"]),
        ("Docker Compose", ["docker", "compose", "version"]),
        ("Git", ["git", "--version"]),
        ("Python", [sys.executable, "--version"]),
    ]

    all_ok = True
    total_checks = len(checks)

    for idx, (name, cmd) in enumerate(checks, 1):
        # Show progress step
        messenger.show_step(idx, total_checks, f"Checking {name}", status="in_progress")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=5
            )
            version = result.stdout.strip().split("\n")[0]

            # Show success with metric
            messenger.show_metric(name, version, icon="✓", color=Colors.SUCCESS)

        except Exception:  # noqa: BLE001
            messenger.show_metric(name, "Not found", icon="✗", color=Colors.ERROR)
            all_ok = False

    click.echo()
    messenger.draw_section("Summary", color=Colors.WARNING)
    click.echo()

    if all_ok:
        messenger.show_success_animation("All dependencies are installed and working!")
        messenger.show_status_badge("System Status", "HEALTHY", success=True)
    else:
        messenger.show_error_animation("Some dependencies are missing")
        messenger.show_status_badge("System Status", "UNHEALTHY", success=False)
        click.echo()
        messenger.show_alert_box(
            "Please install missing dependencies before using DooService.\n"
            "Docker: https://docs.docker.com/get-docker/\n"
            "Git: https://git-scm.com/downloads",
            alert_type="warning",
        )
        sys.exit(1)

    click.echo()


@click.command(name="init")
@click.option(
    "--path",
    "-p",
    default=".",
    help="Directory where to initialize DooService configuration",
)
@click.option(
    "--minimal",
    is_flag=True,
    help="Create minimal configuration (no config/ directory)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing files",
)
def init_cmd(path: str, minimal: bool, force: bool):
    """Initialize DooService configuration in current or specified directory."""
    messenger = ClickMessenger()

    # Get templates directory from shared/templates
    package_dir = Path(__file__).parent.parent
    templates_dir = package_dir / "templates"

    if not templates_dir.exists():
        messenger.error_with_icon("Templates directory not found")
        click.echo(f"Looking for: {templates_dir}")
        sys.exit(1)

    # Target directory
    target_dir = Path(path).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    click.echo()
    messenger.draw_double_box(
        f"DooService Initialization\n{'Minimal' if minimal else 'Complete'} Setup",
        color=Colors.PRIMARY,
    )
    click.echo()

    # Files to copy
    files_to_copy = []

    if minimal:
        # Minimal setup: just main config file
        main_template = templates_dir / "dooservice.yml.template"
        if main_template.exists():
            files_to_copy.append(
                (main_template, target_dir / "dooservice.yml", "Main configuration")
            )
    else:
        # Complete setup: main file + config directory
        main_template = templates_dir / "dooservice.yml.template"
        if main_template.exists():
            files_to_copy.append(
                (main_template, target_dir / "dooservice.yml", "Main configuration")
            )

        # Config directory templates
        config_templates_dir = templates_dir / "config"
        if config_templates_dir.exists():
            config_target_dir = target_dir / "config"
            config_target_dir.mkdir(exist_ok=True)

            for template_file in config_templates_dir.glob("*.template"):
                target_file = config_target_dir / template_file.name.replace(
                    ".template", ""
                )
                files_to_copy.append(
                    (template_file, target_file, f"Config: {template_file.stem}")
                )

    if not files_to_copy:
        messenger.error_with_icon("No template files found")
        sys.exit(1)

    # Copy files with progress
    click.echo(click.style("Creating files:", fg=Colors.SECONDARY, bold=True))
    click.echo()

    copied = 0
    skipped = 0
    overwritten = 0

    for source, target, description in files_to_copy:
        # Check if file exists
        if target.exists() and not force:
            messenger.show_metric(
                description, "SKIPPED (exists)", icon="⊘", color=Colors.WARNING
            )
            skipped += 1
            continue

        try:
            # Copy file
            shutil.copy2(source, target)

            if target.exists() and target.stat().st_mtime > source.stat().st_mtime:
                messenger.show_metric(
                    description, "OVERWRITTEN", icon="↻", color=Colors.WARNING
                )
                overwritten += 1
            else:
                rel_path = str(target.relative_to(target_dir))
                messenger.show_metric(
                    description, rel_path, icon="✓", color=Colors.SUCCESS
                )
                copied += 1

        except Exception as e:  # noqa: BLE001
            messenger.show_metric(
                description, f"FAILED: {str(e)}", icon="✗", color=Colors.ERROR
            )

    # Summary
    click.echo()
    messenger.draw_section("Summary", color=Colors.SUCCESS)
    click.echo()

    if copied > 0:
        messenger.show_metric(
            "Created", f"{copied} files", icon="✓", color=Colors.SUCCESS
        )
    if overwritten > 0:
        messenger.show_metric(
            "Overwritten", f"{overwritten} files", icon="↻", color=Colors.WARNING
        )
    if skipped > 0:
        messenger.show_metric(
            "Skipped", f"{skipped} files", icon="⊘", color=Colors.INFO
        )

    click.echo()
    messenger.show_success_animation("DooService initialized successfully!")
    click.echo()

    # Next steps
    messenger.draw_section("Next Steps", color=Colors.INFO)
    click.echo()
    click.echo(f"  1. Edit {click.style('dooservice.yml', fg=Colors.PRIMARY)}")

    if not minimal:
        click.echo(
            f"  2. Configure {click.style('config/*.yml', fg=Colors.PRIMARY)} files"
        )
        click.echo("  3. Update credentials and settings")
        click.echo("  4. Define your instances")
    else:
        click.echo("  2. Update credentials and settings")
        click.echo("  3. Define your instances")

    click.echo()
    click.echo(
        f"  Run: {click.style('dooservice create <instance_name>', fg=Colors.SUCCESS)}"
    )
    click.echo()
