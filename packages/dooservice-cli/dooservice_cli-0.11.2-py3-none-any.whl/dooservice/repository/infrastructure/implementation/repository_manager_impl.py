from typing import List, Optional

from dooservice.repository.domain.entities.repository_info import (
    RepositoryInfo,
    RepositoryStatus,
)
from dooservice.repository.domain.entities.sync_result import SyncResult
from dooservice.repository.domain.exceptions.repository_exceptions import (
    RepositoryNotFoundError,
    RepositorySyncError,
)
from dooservice.repository.domain.repositories.git_repository import GitRepository
from dooservice.repository.domain.repositories.repository_configuration import (
    RepositoryConfigurationRepository,
)
from dooservice.repository.domain.services.repository_manager import RepositoryManager
from dooservice.shared.messaging import MessageInterface


class RepositoryManagerImpl(RepositoryManager):
    """Implementation of repository manager service."""

    def __init__(
        self,
        git_repository: GitRepository,
        config_repository: RepositoryConfigurationRepository,
        message_interface: MessageInterface,
    ):
        self._git_repository = git_repository
        self._config_repository = config_repository
        self._message_interface = message_interface

    async def list_repositories(
        self, instance_name: str, repo_name: Optional[str] = None
    ) -> List[RepositoryInfo]:
        """List repositories for an instance."""
        # Validate instance exists
        if not self._config_repository.instance_exists(instance_name):
            raise RepositoryNotFoundError(f"Instance '{instance_name}' not found")

        try:
            # Get all repositories for the instance
            repositories = self._config_repository.get_all_repositories_for_instance(
                instance_name
            )

            # Filter by specific repository name if provided
            if repo_name:
                if repo_name not in repositories:
                    raise RepositoryNotFoundError(
                        f"Repository '{repo_name}' not found for instance '{instance_name}'"  # noqa: E501
                    )
                repositories = {repo_name: repositories[repo_name]}

            # Get status for each repository
            repo_infos = []
            for name, repo_config in repositories.items():
                try:
                    # Expand path variables
                    repo_path = self._expand_path_variables(
                        repo_config.path, instance_name
                    )

                    repo_info = self._git_repository.get_repository_status(
                        repo_path=repo_path,
                        repo_url=repo_config.url,
                        repo_branch=repo_config.branch,
                    )
                    repo_info.name = name  # Use config name instead of path-derived name  # noqa: E501
                    repo_info.has_submodules = repo_config.submodules
                    repo_infos.append(repo_info)

                except Exception as e:  # noqa: BLE001
                    self._message_interface.send_warning(
                        f"Error getting status for repository '{name}': {str(e)}"
                    )
                    # Create error repository info
                    repo_info = RepositoryInfo(
                        name=name,
                        url=repo_config.url,
                        branch=repo_config.branch,
                        path=repo_config.path,
                        status=RepositoryStatus.ERROR,
                        error_message=str(e),
                        has_submodules=repo_config.submodules,
                    )
                    repo_infos.append(repo_info)

            return repo_infos

        except RepositoryNotFoundError:
            raise
        except Exception as e:
            raise RepositoryNotFoundError(
                f"Error listing repositories for instance '{instance_name}': {str(e)}"  # noqa: E501
            ) from e

    async def get_repository_status(
        self, instance_name: str, repo_name: str
    ) -> RepositoryInfo:
        """Get status of a specific repository."""
        # Validate instance exists
        if not self._config_repository.instance_exists(instance_name):
            raise RepositoryNotFoundError(f"Instance '{instance_name}' not found")

        # Get repository configuration
        repo_config = self._config_repository.get_repository_by_name(
            repo_name, instance_name
        )
        if not repo_config:
            raise RepositoryNotFoundError(
                f"Repository '{repo_name}' not found for instance '{instance_name}'"
            )

        try:
            # Expand path variables
            repo_path = self._expand_path_variables(repo_config.path, instance_name)

            repo_info = self._git_repository.get_repository_status(
                repo_path=repo_path,
                repo_url=repo_config.url,
                repo_branch=repo_config.branch,
            )
            repo_info.name = repo_name  # Use config name
            repo_info.has_submodules = repo_config.submodules

            return repo_info

        except Exception as e:
            raise RepositoryNotFoundError(
                f"Error getting status for repository '{repo_name}' in instance '{instance_name}': {str(e)}"  # noqa: E501
            ) from e

    async def sync_repositories(
        self,
        instance_name: str,
        repo_name: Optional[str] = None,
        test_mode: bool = False,
    ) -> List[SyncResult]:
        """Sync repositories for an instance."""
        # Validate instance exists
        if not self._config_repository.instance_exists(instance_name):
            raise RepositoryNotFoundError(f"Instance '{instance_name}' not found")

        try:
            # Get repositories to sync
            repositories = self._config_repository.get_all_repositories_for_instance(
                instance_name
            )

            # Filter by specific repository name if provided
            if repo_name:
                if repo_name not in repositories:
                    raise RepositoryNotFoundError(
                        f"Repository '{repo_name}' not found for instance '{instance_name}'"  # noqa: E501
                    )
                repositories = {repo_name: repositories[repo_name]}

            # Sync each repository
            sync_results = []
            for name, repo_config in repositories.items():
                # Only show message if syncing all repos (when repo_name is None)
                # If syncing single repo, the caller will handle the message
                if not repo_name or len(repositories) > 1:
                    self._message_interface.send_info(f"Syncing repository '{name}'...")

                try:
                    # Expand path variables
                    if test_mode:
                        # Use test directory structure for testing
                        repo_path = f"/tmp/dooservice_test/{instance_name}/repos/{name}"  # noqa: S108
                        self._message_interface.send_info(
                            f"Test mode: Using test directory {repo_path}"
                        )
                    else:
                        repo_path = self._expand_path_variables(
                            repo_config.path, instance_name
                        )

                    # Sync repository
                    # Get depth: use config value, default to 1 if not set
                    depth = getattr(repo_config, "depth", 1)
                    sync_result = self._git_repository.sync_repository(
                        repo_url=repo_config.url,
                        repo_path=repo_path,
                        repo_branch=repo_config.branch,
                        include_submodules=repo_config.submodules,
                        ssh_key_path=(
                            repo_config.ssh_key_path
                            if repo_config.ssh_key_path
                            else None  # noqa: E501
                        ),
                        depth=depth,
                    )
                    sync_result.repository_name = name  # Use config name

                    # Only show success/error if syncing all repos
                    if not repo_name or len(repositories) > 1:
                        if sync_result.is_success:
                            self._message_interface.send_success(
                                f"Successfully synced repository '{name}'"
                            )
                        else:
                            self._message_interface.send_error(
                                f"Failed to sync repository '{name}': "
                                f"{sync_result.error_message}"
                            )

                    sync_results.append(sync_result)

                except Exception as e:  # noqa: BLE001
                    error_msg = f"Error syncing repository '{name}': {str(e)}"
                    # Only show error if syncing all repos
                    if not repo_name or len(repositories) > 1:
                        self._message_interface.send_error(error_msg)

                    # Create failed sync result
                    from dooservice.repository.domain.entities.sync_result import (
                        SyncOperation,
                        SyncOperationResult,
                        SyncStatus,
                    )

                    failed_result = SyncResult(
                        repository_name=name,
                        overall_status=SyncStatus.FAILED,
                        operations=[
                            SyncOperationResult(
                                operation=SyncOperation.STATUS_CHECK,
                                status=SyncStatus.FAILED,
                                message=error_msg,
                            )
                        ],
                        error_message=str(e),
                    )
                    sync_results.append(failed_result)

            return sync_results

        except RepositoryNotFoundError:
            raise
        except Exception as e:
            raise RepositorySyncError(
                f"Error syncing repositories for instance '{instance_name}': {str(e)}"  # noqa: E501
            ) from e

    def _expand_path_variables(self, path: str, instance_name: str) -> str:
        """Expand path variables like ${data_dir}, ${instance_name}, etc."""
        # This is a simplified expansion. In a real implementation,
        # you might want to get the actual data_dir from instance configuration
        expanded_path = path.replace("${instance_name}", instance_name)

        # For now, use a simple default data directory structure
        # In a real implementation, you'd get this from the instance configuration
        if "${data_dir}" in expanded_path:
            data_dir = f"/opt/odoo-data/{instance_name}"
            expanded_path = expanded_path.replace("${data_dir}", data_dir)

        return expanded_path
