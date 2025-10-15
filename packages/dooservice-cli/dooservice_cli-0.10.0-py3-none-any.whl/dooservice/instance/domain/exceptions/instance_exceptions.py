class InstanceException(Exception):  # noqa: N818
    """Base exception for instance-related errors."""


class InstanceNotFoundException(InstanceException):
    """Raised when an instance is not found."""

    def __init__(self, instance_name: str = None, message: str = None):
        self.instance_name = instance_name
        if message:
            # Custom message provided (from validator with details)
            super().__init__(message)
        else:
            # Simple instance name provided (backward compatibility)
            super().__init__(f"Instance '{instance_name}' not found")


class InstanceAlreadyExistsException(InstanceException):
    """Raised when trying to create an instance that already exists."""

    def __init__(self, instance_name: str):
        self.instance_name = instance_name
        super().__init__(f"Instance '{instance_name}' already exists")


class InstanceConfigurationException(InstanceException):
    """Raised when there's an error in instance configuration."""

    def __init__(self, message: str, instance_name: str = None):
        self.instance_name = instance_name
        super().__init__(message)


class InstanceOperationException(InstanceException):
    """Raised when an instance operation fails."""

    def __init__(self, message: str, instance_name: str = None):
        self.instance_name = instance_name
        super().__init__(message)


class DockerException(InstanceException):
    """Raised when Docker operations fail."""

    def __init__(self, message: str, container_name: str = None):
        self.container_name = container_name
        super().__init__(message)


class RepositoryException(InstanceException):
    """Raised when repository operations fail."""

    def __init__(self, message: str, repository_name: str = None):
        self.repository_name = repository_name
        super().__init__(message)
