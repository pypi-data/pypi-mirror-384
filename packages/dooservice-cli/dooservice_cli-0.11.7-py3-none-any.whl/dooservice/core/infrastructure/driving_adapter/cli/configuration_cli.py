from pathlib import Path
from typing import Optional

import click

from dooservice.core.domain.exceptions.configuration_exceptions import (
    ConfigurationFileNotFoundException,
    ConfigurationParsingException,
    ConfigurationValidationException,
)
from dooservice.core.infrastructure.driving_adapter.cli.composer import CoreComposer


@click.group(name="config")
def config_cli():
    """Configuration management commands."""


@config_cli.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--no-validate", is_flag=True, help="Skip configuration validation")
def load(file_path: Path, no_validate: bool):
    """Load and validate a configuration file."""
    composer = CoreComposer()
    use_case = composer.get_load_configuration_use_case()

    try:
        configuration = use_case.execute(str(file_path), validate=not no_validate)
        click.echo(f"Configuration loaded successfully from {file_path}")
        click.echo(f"Version: {configuration.version}")
        click.echo(f"Instances: {len(configuration.instances)}")
        click.echo(f"Repositories: {len(configuration.repositories)}")

    except ConfigurationFileNotFoundException as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except ConfigurationValidationException as e:
        click.echo(f"Validation Error: {e}", err=True)
        if e.validation_errors:
            click.echo("Validation errors:", err=True)
            for error in e.validation_errors:
                click.echo(f"  - {error}", err=True)
        raise click.Abort() from e
    except ConfigurationParsingException as e:
        click.echo(f"Parsing Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e


@config_cli.command()
@click.argument("file_path", type=click.Path(path_type=Path))
@click.option("--no-validate", is_flag=True, help="Skip configuration validation")
def create(file_path: Path, no_validate: bool):
    """Create a new configuration file."""
    composer = CoreComposer()
    load_use_case = composer.get_load_configuration_use_case()
    save_use_case = composer.get_save_configuration_use_case()

    try:
        # Try to load existing file for template
        existing = load_use_case.execute(str(file_path), validate=False)
        save_use_case.execute(existing, str(file_path), validate=not no_validate)
        click.echo(f"Configuration file created at: {file_path}")

    except ConfigurationFileNotFoundException:
        # File doesn't exist, create template
        click.echo(f"Creating new configuration file at: {file_path}")
        # Here you could create a default configuration template
        click.echo("Template configuration creation not implemented yet")
    except Exception as e:
        click.echo(f"Error creating configuration: {e}", err=True)
        raise click.Abort() from e


@config_cli.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
def validate(file_path: Path):
    """Validate a configuration file."""
    composer = CoreComposer()
    load_use_case = composer.get_load_configuration_use_case()
    validate_use_case = composer.get_validate_configuration_use_case()

    try:
        configuration = load_use_case.execute(str(file_path), validate=False)
        is_valid = validate_use_case.execute(configuration)

        if is_valid:
            click.echo(f"✓ Configuration file {file_path} is valid")
        else:
            click.echo(f"✗ Configuration file {file_path} has validation errors")
            raise click.Abort()

    except ConfigurationFileNotFoundException as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except ConfigurationParsingException as e:
        click.echo(f"Parsing Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e


@config_cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file path"
)
def convert(input_file: Path, output: Optional[Path]):
    """Convert configuration file format."""
    composer = CoreComposer()
    load_use_case = composer.get_load_configuration_use_case()
    save_use_case = composer.get_save_configuration_use_case()
    repository = composer._repository

    try:
        configuration = load_use_case.execute(str(input_file), validate=True)
        if output:
            save_use_case.execute(configuration, str(output), validate=False)
            click.echo(f"Configuration converted and saved to: {output}")
        else:
            yaml_content = repository.serialize_to_yaml(configuration)
            click.echo(yaml_content)

    except ConfigurationFileNotFoundException as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except ConfigurationValidationException as e:
        click.echo(f"Validation Error: {e}", err=True)
        raise click.Abort() from e
    except ConfigurationParsingException as e:
        click.echo(f"Parsing Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e
