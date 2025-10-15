"""
Instance CLI commands module.

Organizes all CLI commands into logical groups:
- base: Core instance commands (create, delete, start, stop, etc.)
- aliases: Docker/Git-style shortcuts (ls, ps, rm, up, down)
- workflows: Composite commands (deploy, rebuild, destroy)
"""

# Base commands
# Alias commands
from dooservice.instance.infrastructure.driving_adapter.cli.commands.aliases import (
    down_cmd,
    ls_cmd,
    ps_cmd,
    rm_cmd,
    up_cmd,
)
from dooservice.instance.infrastructure.driving_adapter.cli.commands.base import (
    create,
    delete,
    exec_cmd,
    list_cmd,
    logs,
    restart,
    start,
    status,
    stop,
    sync,
    update_modules,
)

# Workflow commands
from dooservice.instance.infrastructure.driving_adapter.cli.commands.workflows import (
    deploy,
    destroy,
    rebuild,
)

__all__ = [
    # Base commands
    "list_cmd",
    "create",
    "delete",
    "start",
    "stop",
    "restart",
    "status",
    "logs",
    "exec_cmd",
    "sync",
    "update_modules",
    # Alias commands
    "ls_cmd",
    "ps_cmd",
    "rm_cmd",
    "up_cmd",
    "down_cmd",
    # Workflow commands
    "deploy",
    "rebuild",
    "destroy",
]
