from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum, auto


class CaptchaState(Enum):
    QUEUED = auto()
    PROCESSING = auto()
    READY = auto()
    FAILED = auto()
    EXPIRED = auto()

class FinalStatus(Enum):
    SUCCESS = "success"
    FAIL = "fail"
    TIMEOUT = "timeout"


@dataclass
class CreateTaskResponseDTO:
    ok: bool
    task_id: Optional[str]
    raw_response: Any
    errors: List[str] = field(default_factory=list)

@dataclass
class StatusResponseDTO:
    state: CaptchaState
    solution: Optional[Any]
    raw_response: Any
    errors: List[str] = field(default_factory=list)

    @property
    def done(self) -> bool:
        return self.state in {CaptchaState.READY, CaptchaState.FAILED, CaptchaState.EXPIRED}

@dataclass
class SolveResultDTO:
    status: FinalStatus
    task_id: Optional[str]
    solution: Optional[Any]
    attempts: int
    response: Any = None
    errors: List[str] = field(default_factory=list)
