from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class RunConfig:
    mode: str
    n: int
    processes: int
    repetition: int

@dataclass
class RunResult:
    config: dict[str, Any]
    result: dict[str, Any]
    command: list[str]
    stdout: str
