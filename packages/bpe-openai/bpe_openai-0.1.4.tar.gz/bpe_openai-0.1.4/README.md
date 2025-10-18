# bpe-openai

[![CI](https://github.com/Pathlit-Inc/bpe-openai/actions/workflows/ci.yml/badge.svg)](https://github.com/Pathlit-Inc/bpe-openai/actions/workflows/ci.yml)
[![Release Wheels](https://github.com/Pathlit-Inc/bpe-openai/actions/workflows/release-wheels.yml/badge.svg)](https://github.com/Pathlit-Inc/bpe-openai/actions/workflows/release-wheels.yml)

`bpe-openai` is a `tiktoken`-compatible tokenizer API backed by the Rust
`bpe-openai` crate. Pathlit maintains the Python wrapper, while the core
tokenizer implementation is developed by GitHub and published in the
[`rust-gems`](https://github.com/github/rust-gems/tree/main/crates/bpe-openai)
project. Published wheels bundle the tokenizer data, so the package works
out of the box on Python 3.9 and newer.

## Installation

```bash
pip install bpe-openai
```

Installing from a source distribution requires a Rust toolchain:

```bash
pip install --no-binary bpe-openai bpe-openai==<version>
```

## Quick start

```python
import bpe_openai as bpe

enc = bpe.get_encoding("cl100k_base")
tokens = enc.encode("Smoke tests keep releases honest.")
print(tokens)
print(enc.decode(tokens))

# Model-aware helper
chat_enc = bpe.encoding_for_model("gpt-4o")
```

## Compatibility snapshot

| API / Feature                             | Status | Notes |
|-------------------------------------------|--------|-------|
| `get_encoding`, `encoding_for_model`      | ✅     | Supports `cl100k_base`, `o200k_base`, `voyage3_base`, and related models |
| `Encoding.encode`, `Encoding.decode`      | ✅     | Rust backend ensures parity with `tiktoken` |
| `Encoding.encode_batch`                   | ✅     | Matches `tiktoken`'s batching behaviour |
| Custom special tokens                     | ⚠️     | Not yet configurable at runtime |
| Legacy GPT-2 / r50k / p50k encodings      | ⚠️     | Planned; current focus is on modern OpenAI models |
| Metrics hook (`set_metrics_hook`)         | ✅     | Emits model, token count, latency, backend version |

Legend: ✅ fully supported · ⚠️ partial / planned

## Why we built it

Long, repetitive prompts can hit pathological slow paths in `tiktoken`. To
stress-test both libraries we encoded inputs of the form `"A" * n` and measured
latency. `bpe-openai` stays effectively flat while `tiktoken` grows sharply with
input length, unlocking workloads like prompt templating and log chunking that
stalled with the reference implementation.

![Encoding time vs. input length](https://raw.githubusercontent.com/Pathlit-Inc/bpe-openai/main/scripts/benchmark_scaling.png)

## Smoke test

After installing from PyPI, run a quick confidence check:

```bash
python - <<'PY'
import bpe_openai as bpe
enc = bpe.get_encoding("cl100k_base")
text = "Smoke tests keep releases honest."
tokens = enc.encode(text)
assert enc.decode(tokens) == text
print("✅ bpe-openai smoke test passed.")
PY
```

## Repository layout

- `python/` – Python package wrapping the Rust tokenizer as a CPython extension.
- `rust/` – Rust crate that loads tokenizer specs and exposes the fast BPE APIs.
- `scripts/` – Helper utilities for benchmarking, parity checks, and data sync.
- `vendor/` – Vendored tokenizer definitions sourced from GitHub's upstream release.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python scripts/sync_tokenizer_data.py  # ensures tokenizer assets are copied
pip install maturin
cd python
maturin develop --release
pytest
```

The repository includes `scripts/sync_tokenizer_data.py` to copy the vendored
`.tiktoken.gz` files into `python/bpe_openai/data/` before building wheels or an
sdist.

## Release process (maintainers)

1. Update the version string in `python/pyproject.toml`. The runtime fallback
   reads the same file, so one change keeps packaging metadata and
   `bpe_openai.__version__` in sync.
2. Run `python scripts/sync_tokenizer_data.py` to refresh bundled assets.
3. Commit the changes and tag the release (`git tag vX.Y.Z`).
4. Push the tag. The `Release Wheels` GitHub Actions workflow builds wheels,
   publishes a GitHub release, and uploads to PyPI via Trusted Publishing.

## Contributing

Contributions are warmly welcomed—whether you are filing a bug, improving
parity with new OpenAI models, or squeezing out more performance. Open an issue
or pull request and the Pathlit team will review quickly.
