from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict, List


@dataclass
class InstancePaths:
    data_dir: Path
    config_file: Path
    addons_dir: Path
    logs_dir: Path
    filestore_dir: Path

    @classmethod
    def from_data_dir(cls, data_dir: str, _: str) -> "InstancePaths":
        base_path = Path(data_dir)
        return cls(
            data_dir=base_path,
            config_file=base_path / "etc" / "odoo.conf",
            addons_dir=base_path / "addons",
            logs_dir=base_path / "logs",
            filestore_dir=base_path / "filestore",
        )


@dataclass
class InstanceEnvironment:
    name: str
    env_vars: Dict[str, str]
    paths: InstancePaths

    def get_addons_paths(self) -> List[str]:
        """Get all addon paths including repos and custom addons directory."""
        addon_paths = []

        # Add base addons directory (mapped to /mnt/extra-addons in container)
        if self.paths.addons_dir.exists():
            addon_paths.append("/mnt/extra-addons")

        # Find addon paths in all repository subdirectories
        if self.paths.addons_dir.exists():
            for repo_dir in self.paths.addons_dir.iterdir():
                if repo_dir.is_dir():
                    # Find addon paths within this repository
                    host_paths = self._find_addon_paths(repo_dir)
                    # Convert host paths to container paths
                    for host_path in host_paths:
                        # Convert /opt/odoo-data/instance/addons/repo/... to
                        # /mnt/extra-addons/repo/...
                        relative_path = host_path.replace(
                            str(self.paths.addons_dir), ""
                        ).lstrip("/")
                        if relative_path:  # Only add non-empty paths
                            container_path = f"/mnt/extra-addons/{relative_path}"
                            addon_paths.append(container_path)

        return addon_paths

    def _find_addon_paths(self, base_path: Path) -> List[str]:
        """Find paths that contain Odoo modules."""
        addon_paths = set()

        for root, _dirs, files in os.walk(str(base_path)):
            if "__manifest__.py" in files or "__openerp__.py" in files:
                addon_paths.add(str(Path(root).parent))

        return sorted(addon_paths)
