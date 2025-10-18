# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""Simplified backup exceptions."""


class BackupError(Exception):
    """Base exception for backup operations."""


class BackupConfigurationError(BackupError):
    """Configuration is invalid or missing."""


class BackupExecutionError(BackupError):
    """Backup execution failed."""
