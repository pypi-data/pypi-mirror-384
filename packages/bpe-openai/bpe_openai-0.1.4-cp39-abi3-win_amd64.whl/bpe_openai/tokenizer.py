from __future__ import annotations

import functools
import importlib
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from typing import AbstractSet, Collection, Literal, Mapping, NoReturn, Optional, Sequence

from . import compat, errors, registry
from .configuration import TokenizerConfiguration, TokenizerRuntime
from .metrics import MetricsPayload, dispatch
from .results import TokenizationResult


_ALLOWED_SPECIAL_ALL = "all"
_DISALLOWED_SPECIAL_ALL = "all"


def _load_backend():
    return importlib.import_module("bpe_openai._bindings")


def _bpe_encode_bytes(mergeable_ranks: Mapping[bytes, int], data: bytes) -> list[int]:
    if not data:
        return []
    parts = [bytes([b]) for b in data]
    while True:
        min_rank = None
        min_idx = None
        for idx in range(len(parts) - 1):
            pair = parts[idx] + parts[idx + 1]
            rank = mergeable_ranks.get(pair)
            if rank is not None and (min_rank is None or rank < min_rank):
                min_rank = rank
                min_idx = idx
        if min_rank is None:
            break
        parts[min_idx : min_idx + 2] = [parts[min_idx] + parts[min_idx + 1]]
    return [mergeable_ranks[part] for part in parts]


class Encoding:
    """tiktoken-compatible encoding interface backed by the Rust tokenizer."""

    def __init__(
        self,
        *,
        name: str,
        model: str,
        runtime: TokenizerRuntime,
        backend,
        backend_version: str,
        pat_str: str,
        mergeable_ranks: dict[bytes, int],
        special_tokens: dict[str, int],
    ) -> None:
        self.name = name
        self._model = model
        self._runtime = runtime
        self._backend = backend
        self._backend_version = backend_version
        self._pat_str = pat_str
        # Copy to guard against accidental mutation of cached dictionaries.
        self._mergeable_ranks = dict(mergeable_ranks)
        self._special_tokens = dict(special_tokens)

        self._metrics_hook = None
        self._last_result: Optional[TokenizationResult] = None

        self._build_rank_tables()

    def __repr__(self) -> str:  # pragma: no cover - formatting helper
        return f"<Encoding {self.name!r}>"

    # ---------------------------------------------------------------------
    # Encoding helpers
    # ---------------------------------------------------------------------

    def encode_ordinary(self, text: str) -> list[int]:
        text = self._sanitize_text(text)
        tokens = self._encode_plain(text)
        self._check_chunk_limit(len(tokens))
        return tokens

    def encode(
        self,
        text: str,
        *,
        allowed_special: Literal["all"] | AbstractSet[str] = frozenset(),
        disallowed_special: Literal["all"] | Collection[str] = "all",
    ) -> list[int]:
        text = self._sanitize_text(text)
        allowed = self._normalize_allowed_special(allowed_special)
        disallowed = self._normalize_disallowed_special(allowed, disallowed_special)

        if disallowed:
            regex = _special_token_regex(disallowed)
            match = regex.search(text)
            if match:
                raise_disallowed_special_token(match.group())

        start = perf_counter()
        tokens = self._encode_with_special(text, allowed)
        elapsed_ms = (perf_counter() - start) * 1_000

        result = TokenizationResult(
            token_ids=tokens,
            token_strings=[],
            total_tokens=len(tokens),
            truncated=False,
            elapsed_ms=elapsed_ms,
        )
        self._last_result = result

        dispatch(
            self._metrics_hook,
            MetricsPayload(
                model=self._model,
                total_tokens=len(tokens),
                elapsed_ms=elapsed_ms,
                rust_backend_version=self._backend_version,
            ),
        )

        return tokens

    def encode_to_numpy(
        self,
        text: str,
        *,
        allowed_special: Literal["all"] | AbstractSet[str] = frozenset(),
        disallowed_special: Literal["all"] | Collection[str] = "all",
    ):
        tokens = self.encode(
            text,
            allowed_special=allowed_special,
            disallowed_special=disallowed_special,
        )
        import numpy as np  # Local import to avoid hard dependency unless needed.

        return np.asarray(tokens, dtype=np.uint32)

    def encode_ordinary_batch(
        self,
        text: Sequence[str],
        *,
        num_threads: int = 8,
    ) -> list[list[int]]:
        def worker(item: str) -> list[int]:
            tokens = self._encode_plain(self._sanitize_text(item))
            self._check_chunk_limit(len(tokens))
            return tokens

        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            return list(pool.map(worker, text))

    def encode_batch(
        self,
        text: Sequence[str],
        *,
        num_threads: int = 8,
        allowed_special: Literal["all"] | AbstractSet[str] = frozenset(),
        disallowed_special: Literal["all"] | Collection[str] = "all",
    ) -> list[list[int]]:
        allowed = self._normalize_allowed_special(allowed_special)
        disallowed = self._normalize_disallowed_special(allowed, disallowed_special)

        def worker(item: str) -> list[int]:
            return self.encode(
                item,
                allowed_special=allowed,
                disallowed_special=disallowed,
            )

        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            return list(pool.map(worker, text))

    def encode_with_unstable(
        self,
        text: str,
        *,
        allowed_special: Literal["all"] | AbstractSet[str] = frozenset(),
        disallowed_special: Literal["all"] | Collection[str] = "all",
    ) -> tuple[list[int], list[list[int]]]:
        raise NotImplementedError(
            "encode_with_unstable is not implemented in bpe-openai; tiktoken compatibility pending"
        )

    def encode_single_token(self, text_or_bytes: str | bytes) -> int:
        if isinstance(text_or_bytes, bytes):
            if text_or_bytes in self._mergeable_ranks:
                return self._mergeable_ranks[text_or_bytes]
            decoded = None
            try:
                decoded = text_or_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise KeyError(f"{text_or_bytes!r} is not a valid token") from exc
            if decoded in self._special_tokens:
                return self._special_tokens[decoded]
            raise KeyError(f"{text_or_bytes!r} is not a valid token")

        text = self._sanitize_text(text_or_bytes)
        if text in self._special_tokens:
            return self._special_tokens[text]
        candidate = self._encode_plain(text)
        if len(candidate) != 1:
            raise KeyError(f"{text_or_bytes!r} does not correspond to a single token")
        return candidate[0]

    def register_special_tokens(self, mapping: Mapping[str, int]) -> None:
        raise NotImplementedError(
            "register_special_tokens is not supported; the underlying tokenizer has a fixed vocabulary"
        )

    # ---------------------------------------------------------------------
    # Decoding helpers
    # ---------------------------------------------------------------------

    def decode_bytes(self, tokens: Sequence[int]) -> bytes:
        chunks = []
        for token in tokens:
            chunk = self._token_to_bytes(token)
            chunks.append(chunk)
        return b"".join(chunks)

    def decode(self, tokens: Sequence[int], errors: str = "replace") -> str:
        return self.decode_bytes(tokens).decode("utf-8", errors=errors)

    def decode_single_token_bytes(self, token: int) -> bytes:
        return self._token_to_bytes(token)

    def decode_tokens_bytes(self, tokens: Sequence[int]) -> list[bytes]:
        return [self._token_to_bytes(token) for token in tokens]

    def decode_with_offsets(
        self,
        tokens: Sequence[int],
    ) -> tuple[str, list[int]]:
        token_bytes = [self._token_to_bytes(token) for token in tokens]

        offsets: list[int] = []
        text_len = 0
        for chunk in token_bytes:
            if chunk:
                offsets.append(max(0, text_len - (0x80 <= chunk[0] < 0xC0)))
                text_len += sum(1 for byte in chunk if not 0x80 <= byte < 0xC0)
            else:
                offsets.append(text_len)

        text = b"".join(token_bytes).decode("utf-8", errors="strict")
        return text, offsets

    def decode_batch(
        self,
        batch: Sequence[Sequence[int]],
        *,
        errors: str = "replace",
        num_threads: int = 8,
    ) -> list[str]:
        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            return list(pool.map(lambda seq: self.decode(seq, errors=errors), batch))

    def decode_bytes_batch(
        self,
        batch: Sequence[Sequence[int]],
        *,
        num_threads: int = 8,
    ) -> list[bytes]:
        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            return list(pool.map(self.decode_bytes, batch))

    # ---------------------------------------------------------------------
    # Misc helpers
    # ---------------------------------------------------------------------

    def token_byte_values(self) -> list[bytes]:
        return list(self._rank_to_bytes)

    @property
    def special_tokens_set(self) -> set[str]:
        return set(self._special_tokens)

    @property
    def n_vocab(self) -> int:
        return self.max_token_value + 1

    def is_special_token(self, token: int) -> bool:
        return token in self._special_token_values

    @property
    def last_result(self) -> Optional[TokenizationResult]:
        return self._last_result

    @property
    def eot_token(self) -> int:
        token = self._special_tokens.get("<|endoftext|>")
        if token is None:
            raise KeyError("<|endoftext|> token is not defined for this encoding")
        return token

    def set_metrics_hook(self, callback) -> None:
        self._metrics_hook = callback
        self._runtime.set_metrics_hook(callback)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_allowed_special(
        self, allowed_special: Literal["all"] | AbstractSet[str]
    ) -> frozenset[str]:
        if allowed_special == _ALLOWED_SPECIAL_ALL:
            return frozenset(self.special_tokens_set)
        return frozenset(allowed_special or [])

    def _normalize_disallowed_special(
        self,
        allowed_special: frozenset[str],
        disallowed_special: Literal["all"] | Collection[str],
    ) -> frozenset[str]:
        if disallowed_special == _DISALLOWED_SPECIAL_ALL:
            return frozenset(self.special_tokens_set - allowed_special)
        return frozenset(disallowed_special or [])

    def _encode_with_special(self, text: str, allowed_special: frozenset[str]) -> list[int]:
        if not allowed_special:
            tokens = self._encode_plain(text)
            self._check_chunk_limit(len(tokens))
            return tokens

        regex = _special_token_regex(allowed_special)
        tokens: list[int] = []
        last_index = 0
        for match in regex.finditer(text):
            if match.start() > last_index:
                tokens.extend(self._encode_plain(text[last_index : match.start()]))
            tokens.append(self._special_tokens[match.group()])
            last_index = match.end()
        if last_index < len(text):
            tokens.extend(self._encode_plain(text[last_index:]))

        self._check_chunk_limit(len(tokens))
        return tokens

    def _encode_plain(self, text: str) -> list[int]:
        if not text:
            return []
        if len(text) >= 1_000_000:
            raise ValueError("Input too long to encode safely")
        try:
            tokens = self._backend.encode(text)
        except UnicodeEncodeError:
            sanitized = self._sanitize_text(text)
            tokens = self._backend.encode(sanitized)
        return list(tokens)

    def _check_chunk_limit(self, total_tokens: int) -> None:
        limit = self._runtime.chunk_limit
        if limit and total_tokens > limit:
            errors.raise_token_limit(total_tokens, limit)

    def _token_to_bytes(self, token: int) -> bytes:
        try:
            chunk = self._rank_to_bytes[token]
        except IndexError as exc:  # pragma: no cover - invalid token
            raise KeyError(f"Token id {token} is out of range for {self.name}") from exc
        if not chunk:
            raise KeyError(f"Token id {token} is not defined for {self.name}")
        return chunk

    def _build_rank_tables(self) -> None:
        max_mergeable = max(self._mergeable_ranks.values(), default=-1)
        max_special = max(self._special_tokens.values(), default=-1)
        self.max_token_value = max(max_mergeable, max_special)
        size = self.max_token_value + 1 if self.max_token_value >= 0 else 0
        self._rank_to_bytes: list[bytes] = [b""] * size
        for token_bytes, rank in self._mergeable_ranks.items():
            if rank >= len(self._rank_to_bytes):
                self._rank_to_bytes.extend([b""] * (rank + 1 - len(self._rank_to_bytes)))
            self._rank_to_bytes[rank] = token_bytes
        for token_str, value in self._special_tokens.items():
            if value >= len(self._rank_to_bytes):
                self._rank_to_bytes.extend([b""] * (value + 1 - len(self._rank_to_bytes)))
            self._rank_to_bytes[value] = token_str.encode("utf-8")
        self.max_token_value = len(self._rank_to_bytes) - 1 if self._rank_to_bytes else -1
        self._special_token_values = frozenset(self._special_tokens.values())

    def _encode_bytes(self, data: bytes) -> list[int]:
        return _bpe_encode_bytes(self._mergeable_ranks, data)

    def _sanitize_text(self, text: str) -> str:
        try:
            text.encode("utf-8")
            return text
        except UnicodeEncodeError:
            return text.encode("utf-16", "surrogatepass").decode("utf-16", "replace")


def build_encoding_from_model(model_name: str) -> Encoding:
    config = TokenizerConfiguration.for_model(model_name)
    runtime = TokenizerRuntime(config)

    encoding_name = config.encoding
    metadata = registry.ENCODING_CONSTRUCTORS[encoding_name]()
    bindings = _load_backend()
    backend = bindings.tokenizer_for_model(model_name)
    backend_version = getattr(bindings, "RUST_BACKEND_VERSION", "unknown")

    return Encoding(
        name=metadata["name"],
        model=model_name,
        runtime=runtime,
        backend=backend,
        backend_version=backend_version,
        pat_str=metadata["pat_str"],
        mergeable_ranks=metadata["mergeable_ranks"],
        special_tokens=metadata["special_tokens"],
    )


def build_encoding_from_name(encoding_name: str) -> Encoding:
    encoding_key = encoding_name.lower()
    if encoding_key not in registry.ENCODING_CONSTRUCTORS:
        raise errors.UnsupportedModelError(
            model_name=encoding_name,
            supported_models=list(registry.ENCODING_CONSTRUCTORS),
        )

    config = TokenizerConfiguration(
        model_name=encoding_key,
        encoding=encoding_key,
        special_tokens=registry.ENCODING_CONSTRUCTORS[encoding_key]()["special_tokens"],
    )
    config.validate()
    runtime = TokenizerRuntime(config)

    metadata = registry.ENCODING_CONSTRUCTORS[encoding_key]()
    bindings = _load_backend()
    backend = bindings.tokenizer_for_encoding(encoding_name)
    backend_version = getattr(bindings, "RUST_BACKEND_VERSION", "unknown")

    return Encoding(
        name=metadata["name"],
        model=encoding_name,
        runtime=runtime,
        backend=backend,
        backend_version=backend_version,
        pat_str=metadata["pat_str"],
        mergeable_ranks=metadata["mergeable_ranks"],
        special_tokens=metadata["special_tokens"],
    )


@functools.lru_cache(maxsize=128)
def _special_token_regex(tokens: AbstractSet[str]):
    if not tokens:
        raise ValueError("Cannot build regex for empty token set")
    try:
        import regex as re  # type: ignore
    except ImportError:  # pragma: no cover - fallback for environments without regex
        import re  # type: ignore
    pattern = "|".join(re.escape(token) for token in tokens)
    return re.compile(f"({pattern})")


def raise_disallowed_special_token(token: str) -> NoReturn:
    raise ValueError(
        f"Encountered text corresponding to disallowed special token {token!r}.\n"
        "If you want this text to be encoded as a special token, "
        f"pass it to `allowed_special`, e.g. `allowed_special={{{token!r}, ...}}`.\n"
        "If you want this text to be encoded as normal text, disable the check for this token "
        f"by passing `disallowed_special=(enc.special_tokens_set - {{{token!r}}})`.\n"
        "To disable this check for all special tokens, pass `disallowed_special=()`.\n"
    )
