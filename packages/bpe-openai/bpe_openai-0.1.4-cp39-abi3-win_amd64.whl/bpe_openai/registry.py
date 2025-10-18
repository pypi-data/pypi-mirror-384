from __future__ import annotations

import base64
import gzip
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Dict

try:  # Python >= 3.9
    from importlib import resources
except ImportError:  # pragma: no cover - fallback
    import importlib_resources as resources  # type: ignore


_DATA_PACKAGE = "bpe_openai.data"
_VENDOR_DATA_DIR = (
    Path(__file__).resolve().parents[2]
    / "vendor"
    / "rust-gems"
    / "crates"
    / "bpe-openai"
    / "data"
)


def _open_tokenizer_data(stem: str):
    resource_name = f"{stem}.tiktoken.gz"
    try:
        return resources.open_binary(_DATA_PACKAGE, resource_name)
    except (FileNotFoundError, ModuleNotFoundError, AttributeError):
        fallback = _VENDOR_DATA_DIR / resource_name
        if not fallback.is_file():  # pragma: no cover - defensive
            raise FileNotFoundError(f"Missing tokenizer data file: {fallback}")
        return open(fallback, "rb")


@lru_cache(maxsize=None)
def _load_mergeable_ranks(stem: str) -> Dict[bytes, int]:
    mergeable: Dict[bytes, int] = {}
    with _open_tokenizer_data(stem) as raw, gzip.open(raw, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            token_b64, rank_str = line.split(" ")
            mergeable[base64.b64decode(token_b64)] = int(rank_str)
    return mergeable


@lru_cache(maxsize=None)
def cl100k_base() -> dict:
    mergeable_ranks = _load_mergeable_ranks("cl100k_base")
    special_tokens = {
        "<|endoftext|>": 100_257,
        "<|fim_prefix|>": 100_258,
        "<|fim_middle|>": 100_259,
        "<|fim_suffix|>": 100_260,
        "<|endofprompt|>": 100_276,
    }
    pat_str = (
        r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| ?[^\s\p{L}\p{N}]++[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s"""
    )
    return {
        "name": "cl100k_base",
        "pat_str": pat_str,
        "mergeable_ranks": mergeable_ranks,
        "special_tokens": special_tokens,
    }


@lru_cache(maxsize=None)
def o200k_base() -> dict:
    mergeable_ranks = _load_mergeable_ranks("o200k_base")
    special_tokens = {
        "<|endoftext|>": 199_999,
        "<|endofprompt|>": 200_018,
    }
    pat_str = "|".join(
        [
            r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?""",
            r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?""",
            r"""\p{N}{1,3}""",
            r""" ?[^\s\p{L}\p{N}]+[\r\n/]*""",
            r"""\s*[\r\n]+""",
            r"""\s+(?!\S)""",
            r"""\s+""",
        ]
    )
    return {
        "name": "o200k_base",
        "pat_str": pat_str,
        "mergeable_ranks": mergeable_ranks,
        "special_tokens": special_tokens,
    }


@lru_cache(maxsize=None)
def voyage3_base() -> dict:
    mergeable_ranks = _load_mergeable_ranks("voyage3_base")
    special_tokens = {
        "<|endoftext|>": 160_255,
        "<|fim_prefix|>": 160_256,
        "<|fim_middle|>": 160_257,
        "<|fim_suffix|>": 160_258,
    }
    pat_str = (
        r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}| ?[^\s\p{L}\p{N}]++[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s"""
    )
    return {
        "name": "voyage3_base",
        "pat_str": pat_str,
        "mergeable_ranks": mergeable_ranks,
        "special_tokens": special_tokens,
    }


ENCODING_CONSTRUCTORS = {
    "cl100k_base": cl100k_base,
    "o200k_base": o200k_base,
    "voyage3_base": voyage3_base,
}


@lru_cache(maxsize=None)
def _openai_public():
    try:
        return import_module("tiktoken_ext.openai_public")
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on install
        raise RuntimeError(
            "tiktoken_ext is required to load legacy encodings (gpt2/r50k/p50k)."
        ) from exc


def _load_openai_public(name: str) -> dict:
    constructor = getattr(_openai_public(), name)
    return constructor()


@lru_cache(maxsize=None)
def gpt2() -> dict:
    return _load_openai_public("gpt2")


@lru_cache(maxsize=None)
def r50k_base() -> dict:
    return _load_openai_public("r50k_base")


@lru_cache(maxsize=None)
def p50k_base() -> dict:
    return _load_openai_public("p50k_base")


@lru_cache(maxsize=None)
def p50k_edit() -> dict:
    return _load_openai_public("p50k_edit")


ENCODING_CONSTRUCTORS.update(
    {
        "gpt2": gpt2,
        "r50k_base": r50k_base,
        "p50k_base": p50k_base,
        "p50k_edit": p50k_edit,
    }
)
