from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RepositoryStatus(Enum):
    NOT_CLONED = "not_cloned"
    CLONED = "cloned"
    UP_TO_DATE = "up_to_date"
    BEHIND = "behind"
    AHEAD = "ahead"
    DIVERGED = "diverged"
    ERROR = "error"


@dataclass
class RepositoryInfo:
    name: str
    url: str
    branch: str
    path: str
    status: RepositoryStatus
    current_commit: Optional[str] = None
    remote_commit: Optional[str] = None
    has_submodules: bool = False
    is_dirty: bool = False
    error_message: Optional[str] = None

    @property
    def is_cloned(self) -> bool:
        return self.status != RepositoryStatus.NOT_CLONED

    @property
    def needs_sync(self) -> bool:
        return self.status in [RepositoryStatus.BEHIND, RepositoryStatus.DIVERGED]
