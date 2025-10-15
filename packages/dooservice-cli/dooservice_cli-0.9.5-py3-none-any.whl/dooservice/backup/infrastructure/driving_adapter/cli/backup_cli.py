"""
Backup CLI with standardized architecture following core module structure.

This module implements backup CLI commands using the same structure as the core module,
with simplified and clean architecture without extra service layers.
"""

from pathlib import Path
from typing import Optional

import click

from dooservice.backup.domain.exceptions.backup_exceptions import (
    BackupConfigurationError,
    BackupExecutionError,
)
from dooservice.backup.infrastructure.driving_adapter.cli.composer import BackupComposer


@click.group(name="backup")
def backup_cli():
    """Backup management commands."""


@backup_cli.command("create")
@click.argument("instance_name")
@click.option("--database", "-d", help="Database name to backup")
@click.option("--format", type=click.Choice(["zip", "dump"]), help="Backup format")
@click.option("--output", "-o", help="Output directory")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def create_backup(
    instance_name: str,
    database: Optional[str],
    format: str,
    output: Optional[str],
    config: str,
    verbose: bool,
):
    """
    Create a backup for INSTANCE_NAME.

    Examples:
      dooservice backup create myapp
      dooservice backup create myapp --database prod --format zip
    """
    import asyncio

    async def _create():
        composer = BackupComposer(config)
        configuration = composer.get_configuration()
        use_case = composer.get_create_backup_use_case()

        output_path = Path(output) if output else None

        return await use_case.execute(
            instance_name=instance_name,
            configuration=configuration,
            database_name=database,
            output_format=format,
            output_path=output_path,
        )

    try:
        metadata = asyncio.run(_create())

        click.echo("✅ Backup created successfully!")
        click.echo(f"📁 File: {metadata.file_path}")
        click.echo(f"📊 Size: {_format_bytes(metadata.file_size)}")
        click.echo(f"🗄️  Database: {metadata.database_name}")

        if verbose:
            click.echo("\n📋 Details:")
            click.echo(f"   Format: {metadata.backup_format}")
            click.echo(f"   Instance: {metadata.instance_name}")
            click.echo(
                f"   Created: {metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            click.echo(f"   Checksum: {metadata.checksum[:16]}...")

    except BackupConfigurationError as e:
        click.echo(click.style(f"Configuration error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except BackupExecutionError as e:
        click.echo(click.style(f"Backup error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e


@backup_cli.command("test")
@click.argument("instance_name")
@click.option("--database", "-d", help="Database name to test")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def test_backup(instance_name: str, database: Optional[str], config: str):
    """
    Test backup connection for INSTANCE_NAME.

    Examples:
      dooservice backup test myapp
      dooservice backup test myapp --database prod
    """
    import asyncio

    async def _test():
        composer = BackupComposer(config)
        configuration = composer.get_configuration()
        use_case = composer.get_test_backup_use_case()

        return await use_case.execute(
            instance_name=instance_name,
            configuration=configuration,
            database_name=database,
        )

    try:
        result = asyncio.run(_test())
        _display_test_results(result)

    except BackupConfigurationError as e:
        click.echo(click.style(f"Configuration error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except BackupExecutionError as e:
        click.echo(click.style(f"Execution error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e


@backup_cli.command("databases")
@click.argument("instance_name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def list_databases(instance_name: str, config: str):
    """
    List databases available for backup in INSTANCE_NAME.

    Examples:
      dooservice backup databases myapp
    """
    import asyncio

    async def _list():
        composer = BackupComposer(config)
        configuration = composer.get_configuration()
        use_case = composer.get_list_databases_use_case()

        return await use_case.execute(
            instance_name=instance_name, configuration=configuration
        )

    try:
        databases = asyncio.run(_list())

        click.echo(f"\n📋 Databases in '{instance_name}':")
        click.echo("-" * 40)
        for db in databases:
            click.echo(f"🗄️  {db}")
        click.echo("-" * 40)
        click.echo(f"Total: {len(databases)} databases")

    except BackupConfigurationError as e:
        click.echo(click.style(f"Configuration error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except BackupExecutionError as e:
        click.echo(click.style(f"Execution error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e


def _display_test_results(result: dict):
    """Display test results in table format."""
    click.echo("\n🧪 Connection Test")
    click.echo("=" * 30)

    if result.get("success"):
        click.echo("✅ Connection: SUCCESS")

        if "version_info" in result:
            version = result["version_info"]
            click.echo(f"📊 Odoo: {version.get('server_version', 'Unknown')}")

        if "databases" in result:
            databases = result["databases"]
            click.echo(f"🗄️  Databases: {len(databases)}")
            for db in databases[:3]:  # Show first 3
                click.echo(f"   • {db}")
            if len(databases) > 3:
                click.echo(f"   ... and {len(databases) - 3} more")

        if "target_db_exists" in result:
            status = "✅ Found" if result["target_db_exists"] else "❌ Not Found"
            click.echo(f"🎯 Target DB: {status}")
    else:
        click.echo("❌ Connection: FAILED")
        if "error" in result:
            click.echo(f"💥 Error: {result['error']}")

    # Show auto-detected values
    if "container_name" in result:
        click.echo(f"\n🐳 Container: {result['container_name']}")
    if "xmlrpc_url" in result:
        click.echo(f"🔗 URL: {result['xmlrpc_url']}")


def _format_bytes(bytes_size: int) -> str:
    """Format bytes into human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"
