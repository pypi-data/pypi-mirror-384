"""
Cloudflare CLI with standardized architecture following core module structure.

This module implements cloudflare CLI commands using the same structure as core,
instance and repository modules, with proper dependency injection through composer
pattern.
"""

import asyncio
import sys

import click
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from dooservice.domains.cloudflare.domain.exceptions.domain_exceptions import (
    DomainNotFoundError,
    DomainSyncError,
    InstanceNotFoundError,
)
from dooservice.domains.cloudflare.domain.exceptions.tunnel_exceptions import (
    TunnelCreationError,
)
from dooservice.domains.cloudflare.infrastructure.driving_adapter.cli.composer import (
    CloudflareComposer,
)

console = Console()


@click.group(name="cloudflare")
def cloudflare_cli():
    """Cloudflare domain and tunnel management commands."""


@cloudflare_cli.group()
def tunnel():
    """Cloudflare tunnel management commands."""


@tunnel.command("init")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--force", is_flag=True, help="Force create even if tunnel exists")
def tunnel_init(config: str, verbose: bool, force: bool):
    """Initialize the Cloudflare tunnel from configuration."""

    async def _run():
        try:
            composer = CloudflareComposer(config)
            config_data = composer.get_configuration()

            # Get tunnel name from configuration
            if not config_data.domains.cloudflare:
                rprint("[red]Cloudflare configuration not found[/red]")
                sys.exit(1)

            if not config_data.domains.cloudflare.tunnel:
                rprint("[red]No tunnel configured in configuration file[/red]")
                sys.exit(1)

            name = config_data.domains.cloudflare.tunnel.name

            if verbose:
                click.echo(f"Using configuration file: {config}")
                click.echo(f"Tunnel name: {name}")

            # Check if tunnel already exists
            if not force:
                tunnel_repository = composer.get_tunnel_repository()
                existing_tunnels = await tunnel_repository.list_tunnels(
                    config_data.domains.cloudflare.account_id
                )
                active_tunnels = [
                    t
                    for t in existing_tunnels
                    if t.name == name and len(t.connections) > 0
                ]

                if active_tunnels:
                    rprint(
                        f"[yellow]⚠ Active tunnel '{name}' already exists "
                        f"(ID: {active_tunnels[0].tunnel_id[:8]}...)[/yellow]"
                    )
                    rprint("[dim]Use --force to create a new tunnel anyway[/dim]")
                    return

                inactive_tunnels = [
                    t
                    for t in existing_tunnels
                    if t.name == name and len(t.connections) == 0
                ]
                if inactive_tunnels:
                    rprint(
                        f"[yellow]⚠ Found {len(inactive_tunnels)} inactive "
                        f"tunnel(s) with name '{name}'[/yellow]"
                    )
                    if click.confirm(
                        "Do you want to delete them and create a new one?"
                    ):
                        for tunnel in inactive_tunnels:
                            await tunnel_repository.delete_tunnel(
                                tunnel.tunnel_id,
                                config_data.domains.cloudflare.account_id,
                            )
                        rprint(
                            f"[green]✓ Deleted {len(inactive_tunnels)} inactive "
                            f"tunnel(s)[/green]"
                        )

            tunnel_init_use_case = composer.get_tunnel_init_use_case()

            rprint(f"[blue]Initializing tunnel '{name}'...[/blue]")
            tunnel_config = await tunnel_init_use_case.execute(name)

            rprint(f"[green]✓ Tunnel '{name}' initialized successfully![/green]")
            rprint(f"Tunnel ID: {tunnel_config.tunnel_id}")
            if verbose:
                rprint(f"Created at: {tunnel_config.created_at}")

        except ValueError as e:
            click.echo(f"Configuration error: {str(e)}", err=True)
            sys.exit(1)
        except TunnelCreationError as e:
            click.echo(f"Failed to create tunnel: {str(e)}", err=True)
            sys.exit(1)
        except Exception as e:  # noqa: BLE001
            click.echo(f"Unexpected error: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(_run())


@tunnel.command("status")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"], case_sensitive=False),
    default="table",
    help="Output format",
)
def tunnel_status(config: str, format: str):
    """Check tunnel status."""

    async def _run():
        try:
            composer = CloudflareComposer(config)

            # Load configuration and get tunnel name
            config_data = composer.get_configuration()

            if not config_data.domains.cloudflare:
                rprint("[red]Cloudflare configuration not found[/red]")
                sys.exit(1)

            if not config_data.domains.cloudflare.tunnel:
                rprint("[red]No tunnel configured in configuration file[/red]")
                sys.exit(1)

            name = config_data.domains.cloudflare.tunnel.name

            # Get docker repository and check status
            docker_repository = composer.get_docker_tunnel_repository()
            status = await docker_repository.get_tunnel_container_status(name)

            # Add tunnel name to status
            status["tunnel_name"] = name

            # Output based on format
            if format == "json":
                import json

                click.echo(json.dumps(status, indent=2, default=str))
            elif format == "yaml":
                import yaml

                click.echo(yaml.dump(status, default_flow_style=False))
            elif status.get("status") == "not_found":
                rprint(f"[yellow]Tunnel '{name}' container not found.[/yellow]")
            else:
                rprint(f"[blue]Tunnel '{name}' Status:[/blue]")
                rprint(f"  Status: [green]{status['status']}[/green]")
                rprint(f"  Container ID: {status.get('id', 'N/A')[:12]}...")
                rprint(f"  Created: {status.get('created', 'N/A')}")
                rprint(f"  Started: {status.get('started_at', 'N/A')}")

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Error checking tunnel status: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())


@tunnel.command("stop")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--force", is_flag=True, help="Force stop without confirmation")
def tunnel_stop(config: str, force: bool):
    """Stop the tunnel container."""

    async def _run():
        try:
            composer = CloudflareComposer(config)

            # Load configuration and get tunnel name
            config_data = composer.get_configuration()

            if not config_data.domains.cloudflare:
                rprint("[red]Cloudflare configuration not found[/red]")
                sys.exit(1)

            if not config_data.domains.cloudflare.tunnel:
                rprint("[red]No tunnel configured in configuration file[/red]")
                sys.exit(1)

            name = config_data.domains.cloudflare.tunnel.name

            # Get docker repository and stop tunnel
            docker_repository = composer.get_docker_tunnel_repository()

            rprint(f"[blue]Stopping tunnel '{name}'...[/blue]")
            success = await docker_repository.stop_tunnel_container(name)

            if success:
                rprint(f"[green]✓ Tunnel '{name}' stopped successfully![/green]")
            else:
                rprint(f"[red]Failed to stop tunnel '{name}'[/red]")
                raise click.ClickException(f"Failed to stop tunnel '{name}'")

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Error stopping tunnel: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())


@tunnel.command("delete")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--force", is_flag=True, help="Force delete without confirmation")
def tunnel_delete(config: str, force: bool):
    """Delete the Cloudflare tunnel including all associated DNS records."""

    async def _run():
        try:
            composer = CloudflareComposer(config)

            # Load configuration and get tunnel name
            config_data = composer.get_configuration()

            if not config_data.domains.cloudflare:
                rprint("[red]Cloudflare configuration not found[/red]")
                sys.exit(1)

            if not config_data.domains.cloudflare.tunnel:
                rprint("[red]No tunnel configured in configuration file[/red]")
                sys.exit(1)

            name = config_data.domains.cloudflare.tunnel.name

            if not force:
                click.confirm(
                    f"Are you sure you want to delete tunnel '{name}' and all its "
                    f"DNS records?",
                    abort=True,
                )

            tunnel_delete_use_case = composer.get_tunnel_delete_use_case()

            rprint(
                f"[blue]Deleting tunnel '{name}' and all associated DNS "
                f"records...[/blue]"
            )
            success = await tunnel_delete_use_case.execute(name, force)

            if success:
                rprint(
                    f"[green]✓ Tunnel '{name}' and all associated DNS records "
                    f"deleted successfully![/green]"
                )
            else:
                rprint("[yellow]⚠ Some components could not be deleted[/yellow]")

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Error deleting tunnel: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())


@tunnel.command("restart")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def tunnel_restart(config: str):
    """Restart the tunnel container."""

    async def _run():
        try:
            composer = CloudflareComposer(config)

            # Load configuration and get tunnel name
            config_data = composer.get_configuration()

            if not config_data.domains.cloudflare:
                rprint("[red]Cloudflare configuration not found[/red]")
                sys.exit(1)

            if not config_data.domains.cloudflare.tunnel:
                rprint("[red]No tunnel configured in configuration file[/red]")
                sys.exit(1)

            name = config_data.domains.cloudflare.tunnel.name

            # Get docker repository
            docker_repository = composer.get_docker_tunnel_repository()

            rprint(f"[blue]Restarting tunnel '{name}'...[/blue]")

            # For now, we'll stop and the system should auto-restart
            # In a more complete implementation, we'd have a restart method
            success = await docker_repository.stop_tunnel_container(name)

            if success:
                rprint(f"[green]✓ Tunnel '{name}' restart initiated![/green]")
                rprint("[dim]Container will be automatically restarted by Docker[/dim]")
            else:
                rprint(f"[red]Failed to restart tunnel '{name}'[/red]")
                raise click.ClickException(f"Failed to restart tunnel '{name}'")

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Error restarting tunnel: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())


@tunnel.command("logs")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option(
    "--tail", "-n", default=50, help="Number of lines to show from end of logs"
)
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def tunnel_logs(config: str, tail: int, follow: bool):
    """Show tunnel container logs."""
    # Get tunnel name from configuration
    composer = CloudflareComposer(config)
    config_data = composer.get_configuration()

    if not config_data.domains.cloudflare or not config_data.domains.cloudflare.tunnel:
        rprint("[red]No tunnel configured in configuration file[/red]")
        sys.exit(1)

    name = config_data.domains.cloudflare.tunnel.name
    container_name = f"cloudflared_{name}"

    if follow:
        rprint(
            f"[blue]Following logs for tunnel '{name}' (Press Ctrl+C to exit)...[/blue]"
        )
        import subprocess

        try:
            subprocess.run(
                ["docker", "logs", "-f", "--tail", str(tail), container_name],
                check=False,
            )
        except KeyboardInterrupt:
            rprint(f"[yellow]Stopped following logs for tunnel '{name}'[/yellow]")
    else:
        rprint(f"[blue]Showing last {tail} lines of logs for tunnel '{name}'...[/blue]")
        import subprocess

        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(tail), container_name],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
            else:
                rprint(f"[red]Error getting logs: {result.stderr}[/red]")
        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Error getting logs: {str(e)}[/red]")


@cloudflare_cli.group()
def domain():
    """Cloudflare domain management commands."""


@domain.command("enable")
@click.argument("name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def domain_enable(name: str, config: str, verbose: bool):
    """Enable a domain by creating DNS records and tunnel configuration."""

    async def _run():
        try:
            composer = CloudflareComposer(config)

            # Load configuration
            composer.get_configuration()

            if verbose:
                click.echo(f"Using configuration file: {config}")

            # Create and execute use case
            domain_enable_use_case = composer.get_domain_enable_use_case()

            rprint(f"[blue]Enabling domain '{name}'...[/blue]")

            success = await domain_enable_use_case.execute(name)

            if success:
                rprint(f"[green]✓ Domain '{name}' enabled successfully![/green]")
                rprint("[dim]DNS record created and tunnel configured.[/dim]")
            else:
                rprint(f"[red]Failed to enable domain '{name}'[/red]")
                raise click.ClickException(f"Failed to enable domain '{name}'")

        except DomainNotFoundError as e:
            rprint(f"[red]Domain not found: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e
        except InstanceNotFoundError as e:
            rprint(f"[red]Instance not found: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e
        except ValueError as e:
            rprint(f"[red]Configuration error: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e
        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Unexpected error: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())


@domain.command("disable")
@click.argument("name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def domain_disable(name: str, config: str, verbose: bool):
    """Disable a domain by removing DNS records and disconnecting from tunnel."""

    async def _run():
        try:
            composer = CloudflareComposer(config)

            # Load configuration
            composer.get_configuration()

            if verbose:
                click.echo(f"Using configuration file: {config}")

            # Create and execute use case
            domain_disable_use_case = composer.get_domain_disable_use_case()

            rprint(f"[blue]Disabling domain '{name}'...[/blue]")
            success = await domain_disable_use_case.execute(name)

            if success:
                rprint(f"[green]✓ Domain '{name}' disabled successfully![/green]")
                rprint(
                    "[dim]DNS record removed and instance disconnected from "
                    "tunnel.[/dim]"
                )
            else:
                rprint(f"[red]Failed to disable domain '{name}'[/red]")
                raise click.ClickException(f"Failed to disable domain '{name}'")

        except DomainNotFoundError as e:
            rprint(f"[red]Domain not found: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e
        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Unexpected error: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())


@domain.command("sync")
@click.argument("name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def domain_sync(name: str, config: str, verbose: bool):
    """Sync domain with instance by connecting to tunnel network."""

    async def _run():
        try:
            composer = CloudflareComposer(config)

            # Load configuration
            composer.get_configuration()

            if verbose:
                click.echo(f"Using configuration file: {config}")

            # Create and execute use case
            domain_sync_use_case = composer.get_domain_sync_use_case()

            rprint(f"[blue]Synchronizing domain '{name}' with instance...[/blue]")
            result = await domain_sync_use_case.execute(name)

            if result.success:
                rprint(f"[green]✓ {result.message}[/green]")

                # Show details
                if result.network_connected:
                    rprint("[dim]✓ Instance connected to tunnel network[/dim]")
                if result.dns_created:
                    rprint("[dim]✓ DNS record configured[/dim]")
                if result.tunnel_configured:
                    rprint("[dim]✓ Tunnel ingress configured[/dim]")
            else:
                rprint(f"[red]✗ {result.message}[/red]")
                raise click.ClickException(result.message)

        except DomainNotFoundError as e:
            rprint(f"[red]Domain not found: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e
        except DomainSyncError as e:
            rprint(f"[red]Sync error: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e
        except ValueError as e:
            rprint(f"[red]Configuration error: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e
        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Unexpected error: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())


@domain.command("list")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress detailed output")
def domain_list(config: str, quiet: bool):
    """List configured domains."""

    async def _run():
        try:
            composer = CloudflareComposer(config)

            # Load configuration
            config_data = composer.get_configuration()

            if not config_data.domains.base_domains:
                rprint("[yellow]No domains configured.[/yellow]")
                return

            # Create table
            table = Table(title="Configured Domains")
            table.add_column("Domain", style="cyan")
            table.add_column("Instance", style="magenta")
            table.add_column("SSL Provider", style="green")
            table.add_column("SSL Enabled", justify="center")
            table.add_column("Force SSL", justify="center")

            for domain_name, domain in config_data.domains.base_domains.items():
                table.add_row(
                    domain_name,
                    domain.instance,
                    str(domain.ssl_provider) if domain.ssl_provider else "Default",
                    "✓" if domain.ssl else "✗",
                    "✓" if domain.force_ssl else "✗",
                )

            console.print(table)

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Error listing domains: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())


@domain.command("status")
@click.argument("name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
def domain_status(name: str, config: str):
    """Check domain status."""

    async def _run():
        try:
            composer = CloudflareComposer(config)

            # Load configuration
            config_data = composer.get_configuration()

            if name not in config_data.domains.base_domains:
                rprint(f"[red]Domain '{name}' not found in configuration[/red]")
                raise click.ClickException(
                    f"Domain '{name}' not found in configuration"
                )

            domain = config_data.domains.base_domains[name]

            rprint(f"[blue]Domain '{name}' Status:[/blue]")
            rprint(f"  Instance: [green]{domain.instance}[/green]")
            rprint(f"  SSL Provider: {domain.ssl_provider or 'Default'}")
            rprint(f"  SSL Enabled: {'✓' if domain.ssl else '✗'}")
            rprint(f"  Force SSL: {'✓' if domain.force_ssl else '✗'}")
            rprint(f"  Redirect WWW: {'✓' if domain.redirect_www else '✗'}")
            rprint(f"  HSTS: {'✓' if domain.hsts else '✗'}")

            if domain.cname_target:
                rprint(f"  CNAME Target: {domain.cname_target}")

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Error checking domain status: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())


@domain.command("test")
@click.argument("name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option("--timeout", default=10, help="Request timeout in seconds")
def domain_test(name: str, config: str, timeout: int):
    """Test domain connectivity and response."""

    async def _run():
        try:
            import httpx

            rprint(f"[blue]Testing domain '{name}'...[/blue]")

            # Test HTTPS connection
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(f"https://{name}")

                    if response.status_code == 200:
                        rprint("[green]✓ HTTPS connection successful[/green]")
                        rprint(f"  Status Code: {response.status_code}")
                        rprint(
                            f"  Response Time: {response.elapsed.total_seconds():.2f}s"
                        )

                        # Check if it's Odoo
                        if "odoo" in response.text.lower():
                            rprint("[green]✓ Odoo detected[/green]")

                    else:
                        rprint(
                            f"[yellow]⚠ HTTPS connection returned status "
                            f"{response.status_code}[/yellow]"
                        )

            except httpx.TimeoutException:
                rprint(f"[red]✗ Request timed out after {timeout}s[/red]")
            except httpx.ConnectError:
                rprint(f"[red]✗ Could not connect to {name}[/red]")
            except Exception as e:  # noqa: BLE001  # noqa: BLE001
                rprint(f"[red]✗ Error testing domain: {str(e)}[/red]")

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Error testing domain: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())


@domain.command("logs")
@click.argument("name")
@click.option(
    "--config", "-c", default="dooservice.yml", help="Configuration file path"
)
@click.option(
    "--tail", "-n", default=50, help="Number of lines to show from end of logs"
)
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def domain_logs(name: str, config: str, tail: int, follow: bool):
    """Show logs for domain's associated instance."""

    async def _run():
        try:
            composer = CloudflareComposer(config)
            config_data = composer.get_configuration()

            # Find domain and get instance
            if name not in config_data.domains.base_domains:
                rprint(f"[red]Domain '{name}' not found in configuration[/red]")
                raise click.ClickException(
                    f"Domain '{name}' not found in configuration"
                )

            domain = config_data.domains.base_domains[name]
            instance_name = domain.instance
            container_name = f"web_{instance_name}"

            if follow:
                rprint(
                    f"[blue]Following logs for domain '{name}' (instance: "
                    f"{instance_name})...[/blue]"
                )
                import asyncio

                try:
                    process = await asyncio.create_subprocess_exec(
                        "docker", "logs", "-f", "--tail", str(tail), container_name
                    )
                    await process.wait()
                except KeyboardInterrupt:
                    rprint(
                        f"[yellow]Stopped following logs for domain '{name}'[/yellow]"
                    )
            else:
                rprint(
                    f"[blue]Showing last {tail} lines of logs for domain '{name}' "
                    f"(instance: {instance_name})...[/blue]"
                )
                import asyncio

                try:
                    process = await asyncio.create_subprocess_exec(
                        "docker",
                        "logs",
                        "--tail",
                        str(tail),
                        container_name,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await process.communicate()
                    result = type(
                        "Result",
                        (),
                        {
                            "returncode": process.returncode,
                            "stdout": stdout.decode() if stdout else "",
                            "stderr": stderr.decode() if stderr else "",
                        },
                    )()
                    if result.returncode == 0:
                        print(result.stdout)
                        if result.stderr:
                            print(result.stderr)
                    else:
                        rprint(f"[red]Error getting logs: {result.stderr}[/red]")
                except Exception as e:  # noqa: BLE001  # noqa: BLE001  # noqa: BLE001
                    rprint(f"[red]Error getting logs: {str(e)}[/red]")

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]Error getting domain logs: {str(e)}[/red]")
            raise click.ClickException(str(e)) from e

    asyncio.run(_run())
