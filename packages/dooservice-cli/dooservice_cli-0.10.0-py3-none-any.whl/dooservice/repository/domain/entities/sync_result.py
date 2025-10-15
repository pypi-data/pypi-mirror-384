from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class SyncOperation(Enum):
    CLONE = "clone"
    PULL = "pull"
    SUBMODULE_UPDATE = "submodule_update"
    STATUS_CHECK = "status_check"


class SyncStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SyncOperationResult:
    operation: SyncOperation
    status: SyncStatus
    message: str
    details: Optional[str] = None


@dataclass
class SyncResult:
    repository_name: str
    overall_status: SyncStatus
    operations: List[SyncOperationResult]
    error_message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.overall_status == SyncStatus.SUCCESS

    @property
    def has_errors(self) -> bool:
        return any(op.status == SyncStatus.FAILED for op in self.operations)
