# Copyright (c) 2025-Present API SERVICE S.A.C. (<https://www.apiservicesac.com/>)

"""Domain exceptions."""


class DomainError(Exception):
    """Base exception for domain operations."""


class DomainNotFoundError(DomainError):
    """Exception raised when domain is not found."""


class DomainSyncError(DomainError):
    """Exception raised when domain synchronization fails."""


class DNSRecordError(DomainError):
    """Exception raised when DNS record operations fail."""


class InstanceNotFoundError(DomainError):
    """Exception raised when instance is not found."""
