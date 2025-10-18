from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


class TokenizerError(RuntimeError):
    """Base class for wrapper-specific errors."""


@dataclass
class UnsupportedModelError(KeyError, TokenizerError):
    model_name: str
    supported_models: Sequence[str]

    def __post_init__(self) -> None:
        supported = ", ".join(sorted(self.supported_models))
        super().__init__(
            f"Model '{self.model_name}' is not supported. Supported models: {supported}"
        )


@dataclass
class SpecialTokenCollisionError(TokenizerError):
    tokens: Sequence[str] | None = None
    ids: Sequence[int] | None = None

    def __post_init__(self) -> None:
        parts: list[str] = []
        if self.tokens:
            parts.append(f"tokens {sorted(self.tokens)}")
        if self.ids:
            parts.append(f"ids {sorted(self.ids)}")
        detail = " and ".join(parts) if parts else "unknown collision"
        super().__init__(f"Special token collision detected for {detail}")


@dataclass
class TokenLimitError(ValueError, TokenizerError):
    token_count: int
    chunk_limit: int

    def __post_init__(self) -> None:
        super().__init__(
            f"Input produces {self.token_count} tokens which exceeds chunk limit {self.chunk_limit}"
        )


def raise_unsupported_model(model_name: str, supported: Iterable[str]) -> None:
    raise UnsupportedModelError(model_name=model_name, supported_models=tuple(sorted(supported)))


def raise_token_limit(token_count: int, chunk_limit: int) -> None:
    raise TokenLimitError(token_count=token_count, chunk_limit=chunk_limit)
