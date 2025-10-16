"""
Repository CLI with standardized architecture following core module structure.

This module implements repository CLI commands using the same structure as the
core module,
with simplified and clean architecture without extra service layers.
"""

from typing import Optional

import click

from dooservice.repository.domain.exceptions.repository_exceptions import (
    RepositoryNotFoundError,
    RepositoryStatusError,
    RepositorySyncError,
)
from dooservice.repository.infrastructure.driving_adapter.cli.composer import (
    RepositoryComposer,
)


@click.group(name="repo")
def repo_cli():
    """Repository management commands."""


@repo_cli.command("list")
@click.argument("instance_name")
@click.option("--repo-name", help="Specific repository name to list")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def list_repositories(instance_name: str, repo_name: Optional[str], config: str):
    """List repositories configured for an instance."""
    import asyncio

    async def _list():
        composer = RepositoryComposer(config)
        use_case = composer.get_list_repositories_use_case()
        return await use_case.execute(instance_name, repo_name)

    try:
        repositories = asyncio.run(_list())

        if not repositories:
            target = f"repository '{repo_name}'" if repo_name else "repositories"
            click.echo(f"No {target} found for instance '{instance_name}'")
            return

        # Display results
        click.echo(f"\nRepositories for instance '{instance_name}':")
        click.echo("-" * 60)

        for repo in repositories:
            _display_repository_info(repo)

    except RepositoryNotFoundError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:  # noqa: BLE001
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e


@repo_cli.command("status")
@click.argument("instance_name")
@click.argument("repo_name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def repository_status(instance_name: str, repo_name: str, config: str):
    """Show detailed status of a specific repository."""
    import asyncio

    async def _status():
        composer = RepositoryComposer(config)
        use_case = composer.get_repository_status_use_case()
        return await use_case.execute(instance_name, repo_name)

    try:
        repo = asyncio.run(_status())

        # Display detailed status
        click.echo(
            f"\nRepository Status: {click.style(repo.name, fg='cyan', bold=True)}"
        )
        click.echo("=" * 50)
        _display_repository_details(repo)

    except RepositoryNotFoundError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except RepositoryStatusError as e:
        click.echo(click.style(f"Status error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:  # noqa: BLE001
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e


@repo_cli.command("sync")
@click.argument("instance_name")
@click.option("--repo-name", help="Specific repository name to sync")
@click.option("--quiet", "-q", is_flag=True, help="Suppress detailed output")
@click.option(
    "--test",
    is_flag=True,
    help="Test mode: clone repositories to temporary test directory",
)
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def sync_repositories(
    instance_name: str, repo_name: Optional[str], quiet: bool, test: bool, config: str
):
    """Synchronize repositories for an instance."""
    import asyncio

    composer = RepositoryComposer(config)
    use_case = composer.get_sync_repositories_use_case()

    try:
        if not quiet:
            target = f"repository '{repo_name}'" if repo_name else "repositories"
            mode_text = " (TEST MODE)" if test else ""
            click.echo(
                f"Synchronizing {target} for instance '{instance_name}'{mode_text}..."
            )

        sync_results = asyncio.run(
            use_case.execute(instance_name, repo_name, test_mode=test)
        )

        if not sync_results:
            click.echo(f"No repositories to sync for instance '{instance_name}'")
            return

        # Display results
        _display_sync_results(sync_results, quiet)

        # Check if any synchronization failed
        failed_count = sum(1 for result in sync_results if not result.is_success)
        if failed_count > 0:
            raise click.Abort()

    except RepositoryNotFoundError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except RepositorySyncError as e:
        click.echo(click.style(f"Sync error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e
    except Exception as e:  # noqa: BLE001
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        raise click.Abort() from e


def _display_repository_info(repo):
    """Display basic repository information."""
    status_color = _get_status_color(repo.status.value)

    click.echo(f"Name: {click.style(repo.name, fg='cyan', bold=True)}")
    click.echo(f"URL: {repo.url}")
    click.echo(f"Branch: {repo.branch}")
    click.echo(f"Path: {repo.path}")
    click.echo(f"Status: {click.style(repo.status.value, fg=status_color)}")

    if repo.current_commit:
        click.echo(f"Current commit: {repo.current_commit}")

    if repo.remote_commit and repo.remote_commit != repo.current_commit:
        click.echo(f"Remote commit: {repo.remote_commit}")

    if repo.has_submodules:
        click.echo(f"Submodules: {click.style('Yes', fg='yellow')}")

    if repo.is_dirty:
        click.echo(f"Status: {click.style('Has uncommitted changes', fg='yellow')}")

    if repo.error_message:
        click.echo(f"Error: {click.style(repo.error_message, fg='red')}")

    click.echo()


def _display_repository_details(repo):
    """Display detailed repository information."""
    status_color = _get_status_color(repo.status.value)

    click.echo(f"URL: {repo.url}")
    click.echo(f"Branch: {repo.branch}")
    click.echo(f"Local path: {repo.path}")
    click.echo(f"Status: {click.style(repo.status.value, fg=status_color)}")

    if repo.current_commit:
        click.echo(f"Current commit: {repo.current_commit}")

    if repo.remote_commit:
        if repo.remote_commit == repo.current_commit:
            click.echo(
                f"Remote commit: {click.style(repo.remote_commit + ' (up to date)', fg='green')}"  # noqa: E501
            )
        else:
            click.echo(f"Remote commit: {click.style(repo.remote_commit, fg='yellow')}")

    click.echo(
        f"Cloned: {click.style('Yes' if repo.is_cloned else 'No', fg='green' if repo.is_cloned else 'red')}"  # noqa: E501
    )

    if repo.has_submodules:
        click.echo(f"Submodules: {click.style('Yes', fg='yellow')}")

    if repo.is_dirty:
        click.echo(
            f"Working directory: {click.style('Has uncommitted changes', fg='yellow')}"
        )
    elif repo.is_cloned:
        click.echo(f"Working directory: {click.style('Clean', fg='green')}")

    if repo.needs_sync:
        click.echo(f"Sync needed: {click.style('Yes', fg='yellow')}")

    if repo.error_message:
        click.echo(f"Error: {click.style(repo.error_message, fg='red')}")


def _display_sync_results(sync_results, quiet):
    """Display synchronization results."""
    success_count = 0
    failed_count = 0

    for result in sync_results:
        if result.is_success:
            success_count += 1
            if not quiet:
                click.echo(
                    f"✓ {click.style(result.repository_name, fg='green')} - Synchronized successfully"  # noqa: E501
                )
        else:
            failed_count += 1
            click.echo(
                f"✗ {click.style(result.repository_name, fg='red')} - Synchronization failed"  # noqa: E501
            )
            if result.error_message:
                click.echo(f"  Error: {result.error_message}")

        # Show operation details if not quiet
        if not quiet:
            for operation in result.operations:
                op_color = "green" if operation.status.value == "success" else "red"
                click.echo(
                    f"  {operation.operation.value}: {click.style(operation.status.value, fg=op_color)} - {operation.message}"  # noqa: E501
                )

    # Summary
    click.echo()
    if success_count > 0:
        click.echo(
            f"Successfully synchronized: {click.style(str(success_count), fg='green')} repositories"  # noqa: E501
        )
    if failed_count > 0:
        click.echo(
            f"Failed to synchronize: {click.style(str(failed_count), fg='red')} repositories"  # noqa: E501
        )


def _get_status_color(status: str) -> str:
    """Get color for repository status."""
    status_colors = {
        "not_cloned": "red",
        "cloned": "yellow",
        "up_to_date": "green",
        "behind": "yellow",
        "ahead": "cyan",
        "diverged": "magenta",
        "error": "red",
    }
    return status_colors.get(status, "white")
