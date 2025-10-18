from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Callable, Dict, Optional


@dataclass(frozen=True)
class MetricsPayload:
    model: str
    total_tokens: int
    elapsed_ms: float
    rust_backend_version: str = "unknown"

    def to_dict(self) -> Dict[str, object]:
        return {
            "model": self.model,
            "total_tokens": self.total_tokens,
            "elapsed_ms": self.elapsed_ms,
            "rust_backend_version": self.rust_backend_version,
        }


def dispatch(hook: Optional[Callable[[Dict[str, object]], None]], payload: MetricsPayload) -> None:
    if hook:
        data = payload.to_dict()
        if data["rust_backend_version"] == "unknown":
            try:
                bindings = import_module("bpe_openai._bindings")
                data["rust_backend_version"] = getattr(
                    bindings, "RUST_BACKEND_VERSION", "unknown"
                )
            except ModuleNotFoundError:  # pragma: no cover - best effort
                pass
        hook(data)
