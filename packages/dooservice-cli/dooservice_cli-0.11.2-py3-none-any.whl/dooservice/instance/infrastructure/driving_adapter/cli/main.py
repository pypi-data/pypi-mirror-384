"""
Instance CLI main orchestrator.

This module aggregates all instance-related CLI commands including:
- Base commands: create, delete, start, stop, restart, sync, etc.
- Aliases: ls, ps, rm, up, down
- Workflows: deploy, rebuild, destroy

Following hexagonal architecture, this is the public interface of the
instance CLI driving adapter.
"""

import click

from dooservice.instance.infrastructure.driving_adapter.cli.commands import (
    create,
    delete,
    deploy,
    destroy,
    down_cmd,
    exec_cmd,
    list_cmd,
    logs,
    ls_cmd,
    ps_cmd,
    rebuild,
    restart,
    rm_cmd,
    start,
    status,
    stop,
    sync,
    up_cmd,
    update_modules,
)


@click.group(name="instance")
def instance_main():
    """
    Instance management commands.

    Quick commands:
      instance create       Create new instance
      instance ls           List instances
      instance up           Start instance
      instance down         Stop instance
      instance deploy       Deploy (create + start)
    """


# Register base instance commands
instance_main.add_command(list_cmd, name="list")
instance_main.add_command(create)
instance_main.add_command(delete)
instance_main.add_command(start)
instance_main.add_command(stop)
instance_main.add_command(restart)
instance_main.add_command(status)
instance_main.add_command(logs)
instance_main.add_command(exec_cmd, name="exec")
instance_main.add_command(sync)
instance_main.add_command(update_modules)

# Register aliases (ls, ps, rm, up, down)
instance_main.add_command(ls_cmd)
instance_main.add_command(ps_cmd)
instance_main.add_command(rm_cmd)
instance_main.add_command(up_cmd)
instance_main.add_command(down_cmd)

# Register workflow commands (deploy, rebuild, destroy)
instance_main.add_command(deploy)
instance_main.add_command(rebuild)
instance_main.add_command(destroy)
