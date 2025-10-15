from typing import Dict, List, Optional

from dooservice.core.domain.entities.configuration import (
    DooServiceConfiguration,
    Repository,
)
from dooservice.repository.domain.exceptions.repository_exceptions import (
    InvalidRepositoryConfigError,
    RepositoryNotFoundError,
)
from dooservice.repository.domain.repositories.repository_configuration import (
    RepositoryConfigurationRepository,
)


class ConfigurationRepositoryImpl(RepositoryConfigurationRepository):
    """Implementation of repository configuration using pre-loaded configuration."""

    def __init__(self, config: DooServiceConfiguration):
        self._config = config

    def get_global_repositories(self) -> Dict[str, Repository]:
        """Get all globally configured repositories."""
        try:
            return self._config.repositories
        except Exception as e:
            raise InvalidRepositoryConfigError(
                f"Failed to load global repositories: {str(e)}"
            ) from e

    def get_instance_repositories(self, instance_name: str) -> Dict[str, Repository]:
        """Get repositories configured for a specific instance."""
        try:
            if instance_name not in self._config.instances:
                raise RepositoryNotFoundError(f"Instance '{instance_name}' not found")

            instance = self._config.instances[instance_name]
            return instance.repositories

        except RepositoryNotFoundError:
            raise
        except Exception as e:
            raise InvalidRepositoryConfigError(
                f"Failed to load repositories for instance '{instance_name}': {str(e)}"
            ) from e

    def get_all_repositories_for_instance(
        self, instance_name: str
    ) -> Dict[str, Repository]:
        """Get all repositories available to an instance.

        Returns global + instance-specific repositories.
        """
        try:
            global_repos = self.get_global_repositories()
            instance_repos = self.get_instance_repositories(instance_name)

            # Get instance configuration to extract addons path for path generation
            if instance_name not in self._config.instances:
                raise RepositoryNotFoundError(f"Instance '{instance_name}' not found")

            addons_path = self._config.instances[instance_name].paths.addons

            # Merge repositories: global + instance-specific overrides
            all_repos = {}

            # Start with global repositories
            all_repos.update(global_repos)

            # Merge instance repositories
            for repo_name, instance_repo in instance_repos.items():
                if repo_name in global_repos:
                    # Merge global + instance config
                    global_repo = global_repos[repo_name]

                    # Special handling for empty instance repositories ({})
                    # Check if instance repo is essentially empty by comparing
                    # with global defaults
                    instance_is_empty = (
                        not hasattr(instance_repo, "url")
                        or not instance_repo.url
                        or instance_repo.url == global_repo.url
                    ) and (
                        not hasattr(instance_repo, "branch")
                        or not instance_repo.branch
                        or
                        # If instance branch equals global branch or default, treat as not overridden  # noqa: E501
                        instance_repo.branch in [global_repo.branch, "main", "master"]
                    )

                    # For empty instance repos, use all global values with only
                    # path override
                    if instance_is_empty:
                        merged_repo = Repository(
                            source_type=global_repo.source_type,
                            path=f"{addons_path}/{repo_name}",
                            type=global_repo.type,
                            url=global_repo.url,
                            branch=global_repo.branch,
                            ssh_key_path=getattr(global_repo, "ssh_key_path", ""),
                            submodules=global_repo.submodules,
                            github=getattr(global_repo, "github", None),
                        )
                    else:
                        # For non-empty instance repos, merge explicitly
                        merged_repo = Repository(
                            source_type=(
                                getattr(instance_repo, "source_type", None)
                                or global_repo.source_type
                            ),
                            path=(
                                getattr(instance_repo, "path", None)
                                or f"{addons_path}/{repo_name}"
                            ),
                            type=(
                                getattr(instance_repo, "type", None) or global_repo.type
                            ),
                            url=(
                                getattr(instance_repo, "url", None) or global_repo.url
                            ),
                            branch=(
                                getattr(instance_repo, "branch", None)
                                or global_repo.branch
                            ),
                            ssh_key_path=(
                                getattr(instance_repo, "ssh_key_path", None)
                                or getattr(global_repo, "ssh_key_path", "")
                            ),
                            submodules=(
                                getattr(instance_repo, "submodules", None)
                                if hasattr(instance_repo, "submodules")
                                else global_repo.submodules
                            ),
                            github=(
                                getattr(instance_repo, "github", None)
                                or getattr(global_repo, "github", None)
                            ),
                        )

                    all_repos[repo_name] = merged_repo
                else:
                    # Instance-only repository
                    if not hasattr(instance_repo, "path") or not instance_repo.path:
                        # Auto-generate path if not specified
                        instance_repo.path = f"{addons_path}/{repo_name}"
                    all_repos[repo_name] = instance_repo

            return all_repos

        except RepositoryNotFoundError:
            raise
        except Exception as e:
            raise InvalidRepositoryConfigError(
                f"Failed to get all repositories for instance '{instance_name}': {str(e)}"  # noqa: E501
            ) from e

    def get_repository_by_name(
        self, repo_name: str, instance_name: Optional[str] = None
    ) -> Optional[Repository]:
        """Get a specific repository by name."""
        try:
            if instance_name:
                # Look in instance-specific repositories first, then global
                all_repos = self.get_all_repositories_for_instance(instance_name)
                return all_repos.get(repo_name)
            # Look only in global repositories
            global_repos = self.get_global_repositories()
            return global_repos.get(repo_name)

        except RepositoryNotFoundError:
            return None
        except Exception as e:
            raise InvalidRepositoryConfigError(
                f"Failed to get repository '{repo_name}': {str(e)}"
            ) from e

    def instance_exists(self, instance_name: str) -> bool:
        """Check if an instance exists in configuration."""
        try:
            return instance_name in self._config.instances
        except Exception:  # noqa: BLE001
            return False

    def get_all_instance_names(self) -> List[str]:
        """Get all instance names from configuration."""
        try:
            return list(self._config.instances.keys())
        except Exception as e:
            raise InvalidRepositoryConfigError(
                f"Failed to get instance names: {str(e)}"
            ) from e
