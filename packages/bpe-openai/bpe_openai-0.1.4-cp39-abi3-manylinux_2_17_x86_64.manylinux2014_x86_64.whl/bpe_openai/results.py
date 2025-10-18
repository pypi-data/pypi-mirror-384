from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class TokenizationResult:
    token_ids: Sequence[int]
    token_strings: Sequence[str]
    total_tokens: int
    truncated: bool
    elapsed_ms: float

    def to_dict(self) -> dict[str, object]:
        return {
            "token_ids": list(self.token_ids),
            "token_strings": list(self.token_strings),
            "total_tokens": self.total_tokens,
            "truncated": self.truncated,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass(frozen=True)
class BenchmarkScenario:
    name: str
    input_source: str
    size_tokens: int
    expected_p50_ms: float
    notes: List[str] = field(default_factory=list)

    def describe(self) -> str:
        return (
            f"Scenario '{self.name}' from {self.input_source} expects "
            f"~{self.size_tokens} tokens @ p50 {self.expected_p50_ms}ms"
        )

