"""Simplified backup configuration."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class BackupConfiguration:
    """Simple backup configuration."""

    admin_password: str
    database_name: str
    output_path: Path
    backup_format: str = "zip"

    def __post_init__(self):
        """Basic validation."""
        if not self.admin_password:
            raise ValueError("admin_password is required")
        if not self.database_name:
            raise ValueError("database_name is required")
        if not isinstance(self.output_path, Path):
            self.output_path = Path(self.output_path)
