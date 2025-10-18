from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, MutableMapping, Optional, Set

from . import compat, errors

DEFAULT_CHUNK_LIMIT = 200_000


SUPPORTED_MODELS: Mapping[str, str] = {
    name: metadata.encoding for name, metadata in compat.MODEL_REGISTRY.items()
}


@dataclass
class TokenizerConfiguration:
    """Configuration information required to build a TokenizerRuntime."""

    model_name: str
    encoding: str
    special_tokens: MutableMapping[str, int] = field(default_factory=dict)
    allowed_special: Set[str] = field(default_factory=set)
    disallowed_special: Set[str] = field(default_factory=set)
    chunk_limit: int = DEFAULT_CHUNK_LIMIT

    def validate(self) -> None:
        if self.chunk_limit <= 0:
            raise ValueError("chunk_limit must be positive")

        collisions = set(self.allowed_special) & set(self.disallowed_special)
        if collisions:
            raise ValueError(
                f"Special token cannot be both allowed and disallowed: {sorted(collisions)}"
            )

        duplicate_ids = self._find_duplicate_ids()
        if duplicate_ids:
            raise errors.SpecialTokenCollisionError(ids=sorted(duplicate_ids))

    def _find_duplicate_ids(self) -> Set[int]:
        seen: Set[int] = set()
        duplicates: Set[int] = set()
        for value in self.special_tokens.values():
            if value in seen:
                duplicates.add(value)
            else:
                seen.add(value)
        return duplicates

    @classmethod
    def for_model(cls, model_name: str) -> "TokenizerConfiguration":
        model = model_name.lower()
        if model not in SUPPORTED_MODELS:
            errors.raise_unsupported_model(model_name, SUPPORTED_MODELS.keys())

        metadata = compat.get_metadata(model)
        special_tokens = dict(metadata.special_tokens)
        config = cls(
            model_name=model,
            encoding=metadata.encoding,
            special_tokens=special_tokens,
            chunk_limit=metadata.chunk_limit,
        )
        config.validate()
        return config


class TokenizerRuntime:
    """Owns tokenizer state and exposes encode/decode operations."""

    def __init__(self, config: TokenizerConfiguration) -> None:
        self.config = config
        self._metrics_hook: Optional[Callable[[dict[str, object]], None]] = None

    def set_metrics_hook(self, callback: Optional[Callable[[dict[str, object]], None]]) -> None:
        self._metrics_hook = callback

    def emit_metrics(self, payload: dict[str, object]) -> None:
        if self._metrics_hook:
            self._metrics_hook(payload)

    @property
    def chunk_limit(self) -> int:
        return self.config.chunk_limit

    def register_special_tokens(self, mapping: Mapping[str, int]) -> None:
        raise NotImplementedError(
            "Custom special tokens are not supported; the underlying tokenizer is fixed."
        )
