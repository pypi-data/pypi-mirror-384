import os
from pathlib import Path
from typing import Optional

import git
from git import GitCommandError, InvalidGitRepositoryError, Repo

from dooservice.repository.domain.entities.repository_info import (
    RepositoryInfo,
    RepositoryStatus,
)
from dooservice.repository.domain.entities.sync_result import (
    SyncOperation,
    SyncOperationResult,
    SyncResult,
    SyncStatus,
)
from dooservice.repository.domain.exceptions.repository_exceptions import (
    RepositoryCloneError,
    RepositorySyncError,
)
from dooservice.repository.domain.repositories.git_repository import GitRepository


class GitPythonAdapter(GitRepository):
    """GitPython implementation for Git operations."""

    def get_repository_status(
        self, repo_path: str, repo_url: str, repo_branch: str
    ) -> RepositoryInfo:
        """Get the status of a repository."""
        try:
            if not self.is_repository_cloned(repo_path):
                return RepositoryInfo(
                    name=os.path.basename(repo_path),
                    url=repo_url,
                    branch=repo_branch,
                    path=repo_path,
                    status=RepositoryStatus.NOT_CLONED,
                )

            repo = Repo(repo_path)

            # Check if dirty (has uncommitted changes)
            is_dirty = repo.is_dirty()

            # Get current commit
            current_commit = (
                repo.head.commit.hexsha[:8] if repo.head.is_valid() else None
            )

            # Check submodules
            has_submodules = len(list(repo.submodules)) > 0

            # Try to fetch remote info
            remote_commit = None
            status = RepositoryStatus.CLONED

            try:
                # Fetch from remote to get latest info
                origin = repo.remotes.origin
                origin.fetch()

                # Get remote commit
                remote_branch = f"origin/{repo_branch}"
                if remote_branch in repo.refs:
                    remote_commit = repo.refs[remote_branch].commit.hexsha[:8]

                    # Compare commits to determine status
                    if current_commit == remote_commit:
                        status = RepositoryStatus.UP_TO_DATE
                    else:
                        # Check if local is behind or ahead
                        commits_behind = list(
                            repo.iter_commits(f"{current_commit}..{remote_branch}")
                        )
                        commits_ahead = list(
                            repo.iter_commits(f"{remote_branch}..{current_commit}")
                        )

                        if commits_behind and commits_ahead:
                            status = RepositoryStatus.DIVERGED
                        elif commits_behind:
                            status = RepositoryStatus.BEHIND
                        elif commits_ahead:
                            status = RepositoryStatus.AHEAD
                        else:
                            status = RepositoryStatus.UP_TO_DATE
            except Exception:  # noqa: BLE001
                # If we can't fetch remote info, just mark as cloned
                status = RepositoryStatus.CLONED

            return RepositoryInfo(
                name=os.path.basename(repo_path),
                url=repo_url,
                branch=repo_branch,
                path=repo_path,
                status=status,
                current_commit=current_commit,
                remote_commit=remote_commit,
                has_submodules=has_submodules,
                is_dirty=is_dirty,
            )

        except Exception as e:  # noqa: BLE001
            return RepositoryInfo(
                name=os.path.basename(repo_path),
                url=repo_url,
                branch=repo_branch,
                path=repo_path,
                status=RepositoryStatus.ERROR,
                error_message=str(e),
            )

    def clone_repository(
        self,
        repo_url: str,
        repo_path: str,
        repo_branch: str,
        ssh_key_path: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> bool:
        """Clone a repository.

        Args:
            repo_url: URL of the repository to clone
            repo_path: Local path where to clone the repository
            repo_branch: Branch to clone
            ssh_key_path: Optional path to SSH key for authentication
            depth: Optional depth for shallow clone (e.g., 1 for only latest commit)
        """
        try:
            # Create parent directory if it doesn't exist
            Path(repo_path).parent.mkdir(parents=True, exist_ok=True)

            # Setup environment for SSH key if provided
            env = os.environ.copy()
            if ssh_key_path and os.path.exists(ssh_key_path):
                env["GIT_SSH_COMMAND"] = (
                    f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no"
                )

            # Clone the repository with optional depth for shallow cloning
            clone_kwargs = {
                "url": repo_url,
                "to_path": repo_path,
                "branch": repo_branch,
                "progress": None,  # Could add progress callback here
            }

            # Add depth for shallow clone if specified (depth > 0)
            # depth == 0 or None means full clone
            if depth and depth > 0:
                clone_kwargs["depth"] = depth

            with git.Git().custom_environment(**env):
                Repo.clone_from(**clone_kwargs)

            return True

        except GitCommandError as e:
            raise RepositoryCloneError(f"Failed to clone repository: {str(e)}") from e
        except Exception as e:
            raise RepositoryCloneError(
                f"Unexpected error during clone: {str(e)}"
            ) from e

    def pull_repository(self, repo_path: str, repo_branch: str) -> bool:
        """Pull latest changes from repository."""
        try:
            repo = Repo(repo_path)
            origin = repo.remotes.origin

            # Checkout the correct branch
            if repo.active_branch.name != repo_branch:
                if repo_branch in repo.heads:
                    repo.heads[repo_branch].checkout()
                else:
                    # Create and checkout new branch tracking origin
                    repo.create_head(repo_branch, f"origin/{repo_branch}").checkout()

            # Pull changes
            origin.pull(repo_branch)

            return True

        except GitCommandError as e:
            raise RepositorySyncError(f"Failed to pull repository: {str(e)}") from e
        except Exception as e:
            raise RepositorySyncError(f"Unexpected error during pull: {str(e)}") from e

    def sync_repository(
        self,
        repo_url: str,
        repo_path: str,
        repo_branch: str,
        include_submodules: bool = False,
        ssh_key_path: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> SyncResult:
        """Synchronize repository (clone if needed, pull if exists).

        Args:
            repo_url: URL of the repository
            repo_path: Local path of the repository
            repo_branch: Branch to sync
            include_submodules: Whether to update submodules
            ssh_key_path: Optional SSH key path for authentication
            depth: Optional depth for shallow clone (only used for initial clone)
        """
        operations = []
        overall_status = SyncStatus.SUCCESS
        error_message = None

        try:
            # Check if repository is already cloned
            if not self.is_repository_cloned(repo_path):
                # Clone repository
                try:
                    self.clone_repository(
                        repo_url, repo_path, repo_branch, ssh_key_path, depth
                    )
                    operations.append(
                        SyncOperationResult(
                            operation=SyncOperation.CLONE,
                            status=SyncStatus.SUCCESS,
                            message=f"Successfully cloned repository to {repo_path}",
                        )
                    )
                except Exception as e:  # noqa: BLE001
                    operations.append(
                        SyncOperationResult(
                            operation=SyncOperation.CLONE,
                            status=SyncStatus.FAILED,
                            message=f"Failed to clone repository: {str(e)}",
                        )
                    )
                    overall_status = SyncStatus.FAILED
                    error_message = str(e)
            else:
                # Pull latest changes
                try:
                    self.pull_repository(repo_path, repo_branch)
                    operations.append(
                        SyncOperationResult(
                            operation=SyncOperation.PULL,
                            status=SyncStatus.SUCCESS,
                            message="Successfully pulled latest changes",
                        )
                    )
                except Exception as e:  # noqa: BLE001
                    operations.append(
                        SyncOperationResult(
                            operation=SyncOperation.PULL,
                            status=SyncStatus.FAILED,
                            message=f"Failed to pull changes: {str(e)}",
                        )
                    )
                    overall_status = SyncStatus.FAILED
                    error_message = str(e)

            # Update submodules if requested and operation was successful so far
            if include_submodules and overall_status == SyncStatus.SUCCESS:
                try:
                    self.update_submodules(repo_path)
                    operations.append(
                        SyncOperationResult(
                            operation=SyncOperation.SUBMODULE_UPDATE,
                            status=SyncStatus.SUCCESS,
                            message="Successfully updated submodules",
                        )
                    )
                except Exception as e:  # noqa: BLE001
                    operations.append(
                        SyncOperationResult(
                            operation=SyncOperation.SUBMODULE_UPDATE,
                            status=SyncStatus.FAILED,
                            message=f"Failed to update submodules: {str(e)}",
                        )
                    )
                    overall_status = SyncStatus.FAILED
                    error_message = str(e)

            # Final status check
            try:
                repo_info = self.get_repository_status(repo_path, repo_url, repo_branch)
                status_message = f"Repository status: {repo_info.status.value}"
                if repo_info.current_commit:
                    status_message += f" (commit: {repo_info.current_commit})"

                operations.append(
                    SyncOperationResult(
                        operation=SyncOperation.STATUS_CHECK,
                        status=SyncStatus.SUCCESS,
                        message=status_message,
                    )
                )
            except Exception as e:  # noqa: BLE001
                operations.append(
                    SyncOperationResult(
                        operation=SyncOperation.STATUS_CHECK,
                        status=SyncStatus.FAILED,
                        message=f"Failed to check status: {str(e)}",
                    )
                )

        except Exception as e:  # noqa: BLE001
            overall_status = SyncStatus.FAILED
            error_message = str(e)
            operations.append(
                SyncOperationResult(
                    operation=SyncOperation.STATUS_CHECK,
                    status=SyncStatus.FAILED,
                    message=f"Unexpected error during sync: {str(e)}",
                )
            )

        return SyncResult(
            repository_name=os.path.basename(repo_path),
            overall_status=overall_status,
            operations=operations,
            error_message=error_message,
        )

    def update_submodules(self, repo_path: str) -> bool:
        """Update repository submodules."""
        try:
            repo = Repo(repo_path)

            # Initialize and update submodules
            for submodule in repo.submodules:
                submodule.update(init=True, recursive=True)

            return True

        except GitCommandError as e:
            raise RepositorySyncError(f"Failed to update submodules: {str(e)}") from e
        except Exception as e:  # noqa: BLE001
            raise RepositorySyncError(
                f"Unexpected error updating submodules: {str(e)}"
            ) from e

    def is_repository_cloned(self, repo_path: str) -> bool:
        """Check if repository is already cloned."""
        try:
            if not os.path.exists(repo_path):
                return False

            # Try to create a Repo object
            Repo(repo_path)
            return True

        except (InvalidGitRepositoryError, GitCommandError):
            return False
        except Exception:  # noqa: BLE001
            return False
