# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""Shared CLI components for DooService."""

from dooservice.shared.cli_components.interactive import select_instance
from dooservice.shared.cli_components.ordered_group import OrderedGroup
from dooservice.shared.cli_components.system_commands import doctor_cmd, init_cmd

__all__ = ["OrderedGroup", "doctor_cmd", "init_cmd", "select_instance"]
