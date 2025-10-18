# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""
Instance CLI commands module.

Organizes all CLI commands into logical groups:
- base_commands: Core instance commands (create, delete, start, stop, etc.)
- alias_commands: Docker/Git-style shortcuts (ls, ps, rm, up, down)
- workflow_commands: Composite commands (deploy, rebuild, destroy)
"""

# Base commands
# Alias commands
from dooservice.instance.infrastructure.driving_adapter.cli.commands.alias_commands import (  # noqa: E501
    down_cmd,
    ls_cmd,
    ps_cmd,
    rm_cmd,
    up_cmd,
)
from dooservice.instance.infrastructure.driving_adapter.cli.commands.base_commands import (  # noqa: E501
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
from dooservice.instance.infrastructure.driving_adapter.cli.commands.workflow_commands import (  # noqa: E501
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
