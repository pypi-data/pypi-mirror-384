from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

from . import registry


@dataclass(frozen=True)
class ModelMetadata:
    encoding: str
    chunk_limit: int
    special_tokens: Mapping[str, int]


def _metadata(
    encoding: str,
    chunk_limit: int = 200_000,
    special_tokens: Mapping[str, int] | None = None,
) -> ModelMetadata:
    tokens = special_tokens
    if tokens is None:
        tokens = registry.ENCODING_CONSTRUCTORS[encoding]()["special_tokens"]
    return ModelMetadata(
        encoding=encoding,
        chunk_limit=chunk_limit,
        special_tokens=tokens,
    )


MODEL_REGISTRY: Dict[str, ModelMetadata] = {
    "cl100k_base": _metadata("cl100k_base"),
    "o200k_base": _metadata("o200k_base"),
    "voyage3_base": _metadata("voyage3_base"),
    "gpt-4o": _metadata("o200k_base"),
    "gpt-4o-mini": _metadata("o200k_base"),
    "gpt-4.1": _metadata("o200k_base"),
    "gpt-4.1-mini": _metadata("o200k_base"),
    "gpt-4o-128k": _metadata("o200k_base"),
    "gpt-4.1-128k": _metadata("o200k_base"),
    "voyage-3": _metadata("voyage3_base"),
    "gpt-3.5": _metadata("cl100k_base"),
    "gpt-3.5-turbo": _metadata("cl100k_base"),
    "gpt-3.5-turbo-0301": _metadata("cl100k_base"),
    "gpt-3.5-turbo-0401": _metadata("cl100k_base"),
    "gpt-3.5-turbo-0125": _metadata("cl100k_base"),
    "gpt-35-turbo": _metadata("cl100k_base"),
    "gpt-4": _metadata("cl100k_base"),
    "gpt-4-0314": _metadata("cl100k_base"),
    "gpt-4-0613": _metadata("cl100k_base"),
    "gpt-4-32k": _metadata("cl100k_base"),
    "gpt2": _metadata("gpt2", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "gpt-2": _metadata("gpt2", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "r50k_base": _metadata("r50k_base", chunk_limit=4_096, special_tokens={"<|endoftext|>": 50_256}),
    "p50k_base": _metadata("p50k_base", chunk_limit=4_096, special_tokens={"<|endoftext|>": 50_256}),
    "p50k_edit": _metadata(
        "p50k_edit",
        chunk_limit=4_096,
        special_tokens={
            "<|endoftext|>": 50_256,
            "<|fim_prefix|>": 50_281,
            "<|fim_middle|>": 50_282,
            "<|fim_suffix|>": 50_283,
        },
    ),
    "text-davinci-003": _metadata("p50k_base", chunk_limit=4_096, special_tokens={"<|endoftext|>": 50_256}),
    "text-davinci-002": _metadata("p50k_base", chunk_limit=4_096, special_tokens={"<|endoftext|>": 50_256}),
    "text-davinci-001": _metadata("r50k_base", chunk_limit=4_096, special_tokens={"<|endoftext|>": 50_256}),
    "text-curie-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "text-babbage-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "text-ada-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "davinci": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "curie": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "babbage": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "ada": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "code-davinci-002": _metadata("p50k_base", chunk_limit=8_000, special_tokens={"<|endoftext|>": 50_256}),
    "code-davinci-001": _metadata("p50k_base", chunk_limit=8_000, special_tokens={"<|endoftext|>": 50_256}),
    "code-cushman-002": _metadata("p50k_base", chunk_limit=8_000, special_tokens={"<|endoftext|>": 50_256}),
    "code-cushman-001": _metadata("p50k_base", chunk_limit=8_000, special_tokens={"<|endoftext|>": 50_256}),
    "davinci-codex": _metadata("p50k_base", chunk_limit=8_000, special_tokens={"<|endoftext|>": 50_256}),
    "cushman-codex": _metadata("p50k_base", chunk_limit=8_000, special_tokens={"<|endoftext|>": 50_256}),
    "text-davinci-edit-001": _metadata(
        "p50k_edit",
        chunk_limit=8_000,
        special_tokens={
            "<|endoftext|>": 50_256,
            "<|fim_prefix|>": 50_281,
            "<|fim_middle|>": 50_282,
            "<|fim_suffix|>": 50_283,
        },
    ),
    "code-davinci-edit-001": _metadata(
        "p50k_edit",
        chunk_limit=8_000,
        special_tokens={
            "<|endoftext|>": 50_256,
            "<|fim_prefix|>": 50_281,
            "<|fim_middle|>": 50_282,
            "<|fim_suffix|>": 50_283,
        },
    ),
    "text-similarity-davinci-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "text-similarity-curie-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "text-similarity-babbage-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "text-similarity-ada-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "text-search-davinci-doc-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "text-search-curie-doc-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "text-search-babbage-doc-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "text-search-ada-doc-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "code-search-babbage-code-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "code-search-ada-code-001": _metadata("r50k_base", chunk_limit=2_048, special_tokens={"<|endoftext|>": 50_256}),
    "text-embedding-ada-002": _metadata("cl100k_base", chunk_limit=8_192, special_tokens={}),
    "text-embedding-3-small": _metadata("cl100k_base", chunk_limit=8_192, special_tokens={}),
    "text-embedding-3-large": _metadata("cl100k_base", chunk_limit=8_192, special_tokens={}),
}


def list_supported_models() -> list[str]:
    return sorted(MODEL_REGISTRY)


def get_metadata(model_name: str) -> ModelMetadata:
    key = model_name.lower()
    try:
        return MODEL_REGISTRY[key]
    except KeyError as exc:  # pragma: no cover - handled by higher-level error
        raise KeyError(model_name) from exc


def get_default_special_tokens(encoding_name: str) -> Mapping[str, int]:
    metadata = MODEL_REGISTRY.get(encoding_name.lower())
    if metadata:
        return metadata.special_tokens
    # Fallback to primary model metadata if encoding maps elsewhere.
    for item in MODEL_REGISTRY.values():
        if item.encoding == encoding_name:
            return item.special_tokens
    return {}
