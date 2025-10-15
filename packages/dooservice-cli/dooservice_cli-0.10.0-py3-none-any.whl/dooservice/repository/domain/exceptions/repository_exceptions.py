class RepositoryError(Exception):
    """Base exception for repository operations."""


class RepositoryNotFoundError(RepositoryError):
    """Repository not found in configuration."""


class RepositoryCloneError(RepositoryError):
    """Error cloning repository."""


class RepositorySyncError(RepositoryError):
    """Error synchronizing repository."""


class RepositoryStatusError(RepositoryError):
    """Error checking repository status."""


class InvalidRepositoryConfigError(RepositoryError):
    """Invalid repository configuration."""
