"""Interactive helper functions for CLI."""

import questionary

from dooservice.core.domain.entities.configuration import DooServiceConfiguration


def select_instance(
    config_data: DooServiceConfiguration,
    message: str = "Select an instance",
) -> str:
    """Show interactive menu to select an instance.

    Args:
        config_data: Configuration data
        message: Message to display

    Returns:
        Selected instance name

    Raises:
        click.Abort: If user cancels selection
    """
    if not config_data.instances:
        import click

        click.echo("No instances found in configuration")
        raise click.Abort()

    instance_names = list(config_data.instances.keys())

    if len(instance_names) == 1:
        # Only one instance, return it directly
        return instance_names[0]

    # Show interactive menu
    selected = questionary.select(
        message,
        choices=instance_names,
    ).ask()

    if selected is None:
        # User cancelled
        import click

        raise click.Abort()

    return selected
