"""Simplified backup exceptions."""


class BackupError(Exception):
    """Base exception for backup operations."""


class BackupConfigurationError(BackupError):
    """Configuration is invalid or missing."""


class BackupExecutionError(BackupError):
    """Backup execution failed."""
