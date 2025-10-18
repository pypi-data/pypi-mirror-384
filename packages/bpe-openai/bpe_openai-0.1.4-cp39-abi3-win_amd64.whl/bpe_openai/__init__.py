"""Tiktoken-compatible wrapper exposing the bpe-openai Rust tokenizer crate."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path
from typing import Iterable

from . import compat
from .errors import (
    SpecialTokenCollisionError,
    TokenLimitError,
    TokenizerError,
    UnsupportedModelError,
)
from .tokenizer import Encoding, build_encoding_from_model, build_encoding_from_name

def _local_version() -> str:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        content = pyproject.read_text(encoding="utf-8")
    except FileNotFoundError:  # pragma: no cover - defensive fallback
        return "0.0.0"

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("version = "):
            _, value = stripped.split("=", 1)
            value = value.split("#", 1)[0].strip()
            return value.strip('"\'')
    return "0.0.0"


try:  # pragma: no cover - package metadata unavailable during local dev
    __version__ = metadata.version("bpe-openai")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = _local_version()

__all__ = [
    "Encoding",
    "encoding_for_model",
    "encoding_name_for_model",
    "get_encoding",
    "list_supported_models",
    "list_encoding_names",
    "TokenizerError",
    "UnsupportedModelError",
    "SpecialTokenCollisionError",
    "TokenLimitError",
    "__version__",
]


def list_supported_models() -> list[str]:
    return compat.list_supported_models()


def encoding_for_model(model_name: str) -> Encoding:
    return build_encoding_from_model(model_name)


def get_encoding(encoding_name: str) -> Encoding:
    return build_encoding_from_name(encoding_name)


def list_encoding_names() -> list[str]:
    from . import registry

    return sorted(registry.ENCODING_CONSTRUCTORS)


def encoding_name_for_model(model_name: str) -> str:
    metadata = compat.get_metadata(model_name)
    return metadata.encoding
