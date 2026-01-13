# AI Context: `lstring` (True Python Lazy String)

This file is intended primarily for AI agents and automated tooling that need to **extend, optimize, or integrate** this repository into larger Python projects.

## 0) What this project is

- **Package name (PyPI / import):** `lstring`
- **Native extension module:** `_lstring` (C++ CPython extension)
- **Main exported type:** `lstring.L` (lazy/rope-like Unicode string)
- **Core idea:** Most string operations build a *lazy* representation (a small tree of buffers). Actual materialization to a real `str` happens only when required.

## AI-assisted development note

This repository is developed and maintained with the help of AI-assisted tooling. A short disclosure and an up-to-date list of models/tools used is maintained in the project README.

## 1) When to use `L` in user projects

Use `L` when the workload creates many intermediate strings (templating, pipelines, slicing/concatenation-heavy code), especially when:

- You can keep values as `L` for most of the pipeline, converting to `str` only at boundaries.
- You expect many `+`, slicing, joining, formatting operations.

Avoid / be cautious when:

- You repeatedly call operations that are implemented by delegating to CPython via `str(...)` (these will materialize).
- You require a stable `repr()` format as part of a public contract. `repr(L(...))` is for debugging/testing only.

## 2) Public API surface (what user code should rely on)

From Python:

```python
from lstring import L, CharClass, get_optimize_threshold, set_optimize_threshold
```

- `L`: the lazy string type (Python wrapper around `_lstring.L`).
- `CharClass`: `IntFlag` enum for character classes used by non-standard search methods.
- `get_optimize_threshold()` / `set_optimize_threshold(threshold: int)`:
  - **Process-global knob** that controls whether *small* results should be materialized into a simple `L` backed by `str`.

Non-standard search methods on `L` (intended for performance):

- `findc`, `rfindc`: find a single character.
- `findcs`, `rfindcs`: find any character from a set (`str` or `L`), with optional `invert`.
- `findcr`, `rfindcr`: find any character from a codepoint range.
- `findcc`, `rfindcc`: find any character from a `CharClass` mask.

## 3) Critical invariants and contracts (do not break casually)

### Immutability

- `L` is **immutable at the public API level**: operations never modify an existing `L` in place.
- Internals may update **caches** (e.g., cached lengths/heights) for performance; this is not observable via the public API.

### Representation stability

- `repr(L(...))` is **not** a stable public API.
- Some tests parse `repr()` to validate *structural properties* (e.g., balanced concatenation trees). If you change `repr()` output, you must adjust these tests accordingly.

### Materialization

- Materialization to `str` must be **explicit** (e.g., `str(L)`), or happen only where the design intentionally delegates to CPython for compatibility.

### Optimize threshold

- `set_optimize_threshold()` is **process-global**.
- Tests that depend on deterministic structure often disable it (`set_optimize_threshold(0)`).

## 4) Build / install / test (facts)

### Build system

- `pyproject.toml` declares build requirements: `setuptools`, `wheel`, `cppy`.
- `setup.py` defines the C++ extension and sources.

### Editable install (local dev)

```bash
python -m pip install -U pip
python -m pip install -U .
```

### Tests

```bash
python -m unittest discover -v
```

The repository also contains a VS Code task that runs coverage + LCOV (see `.vscode/tasks.json` in your editor task list).

### IMPORTANT: avoid importing a stale local `_lstring*.so`

If you ever have a stray `_lstring*.so` in the repository root (from a previous local build), Python may import it instead of the intended extension. If you see confusing behavior after rebuilds, remove it:

```bash
rm -f ./_lstring*.so
```

## 5) Code map (where to look)

### Python package glue

- `lstring/__init__.py`: public re-exports (`L`, `CharClass`, optimize-threshold functions).
- `lstring/lstring.py`: Python wrapper class `L(_lstring.L)` plus Python-level convenience methods.
- `lstring/format.py`: formatting helpers used by `L.format`, `%`, `L.f()`.

### C++ extension core

- `src/lstring_module.cxx`: module-level exports (including `set_optimize_threshold`).
- `src/lstring.cxx`: `_lstring.L` type and core operators (`__add__`, slicing, `*`, iteration, etc.).
- `src/lstring_concat.cxx`: **balanced concatenation** implementation (`concat_balanced` + rotations).
- `src/lstring_methods.cxx`: method table and many `L.*` methods, including non-standard search.
- `src/buffer.cxx`: `Buffer` base implementation, shared `findcs/rfindcs` loops, manual RTTI `is_a`.

### Buffer types (lazy representation)

- `src/str_buffer.hxx`: simple buffer backed by a real `str`.
- `src/join_buffer.hxx`: concatenation node (`left + right`), with cached `length()` and `height()`.
- `src/mul_buffer.hxx`: repetition (`base * n`), with cached `length()`.
- `src/slice_buffer.hxx`:
  - `Slice1Buffer`: contiguous slice (`step == 1`), with cached `length()`.
  - `SliceBuffer`: stepped slice (`step != 1`).

### Tests

- `tests/`: extensive `unittest` coverage.
- `tests/test_lstr_balanced_concat_repr.py`: validates that repeated `+` results in a roughly `O(log n)` concatenation tree height (by parsing `repr()`).

### Benchmarks

- `benchmarks/` and top-level `benchmark_*.py`: microbenchmarks.

## 6) Performance model (how to optimize correctly)

### Key hot paths

- Repeated concatenation (`+`) should not degenerate into a linear rope.
  - The project enforces balancing via `concat_balanced`.
- `findcs/rfindcs` performance depends heavily on charset representation.
  - Internal `CharSet` strategies exist to speed membership tests.

### Caches

Some composite buffers cache properties lazily (e.g., `JoinBuffer.length()`, `JoinBuffer.height()`, `MulBuffer.length()`, `Slice1Buffer.length()`).

Do:

- Keep caches logically immutable (cache updates are OK, but must not change semantics).
- Ensure caches are safe across repeated calls.

Do not:

- Introduce observable mutation (changing `repr`/`str` output) as a side effect of calling `length()` / `height()`.

### Materialization vs laziness

If you implement new methods, decide explicitly:

- **Lazy implementation:** returns a compound `L` that defers work.
- **Delegating implementation:** converts to `str` and calls CPython, trading laziness for compatibility.

Document the decision in the method docstring and keep it consistent.

## 7) How to add/modify functionality (agent checklist)

When adding a new performance-sensitive feature:

1. Decide whether it belongs in C++ (`src/*.cxx`, `src/*.hxx`) or in Python (`lstring/lstring.py`).
2. For C++ methods on `L`:
   - Add an entry in the method table in `src/lstring_methods.cxx`.
   - Implement the function with correct reference counting and error handling.
3. Add tests under `tests/` (prefer deterministic tests; disable optimize threshold when checking `repr()` structure).
4. Consider adding/adjusting a benchmark under `benchmarks/`.

## 8) Gotchas / common failure modes

- **Stale extension import:** a leftover `./_lstring*.so` can shadow the built package.
- **Optimize threshold:** it is process-global; tests/benchmarks should set it explicitly.
- **`repr()` structure tests:** changes to balancing or representation may require updating parsing-based tests.
- **Unicode complexity:** prefer using existing low-level helpers/strategies instead of re-implementing naïve scans.

## 9) What an AI agent should not do

- Do not treat `repr(L(...))` as a stable API for downstream users.
- Do not add new public methods that violate immutability-by-interface.
- Do not “optimize” by eagerly materializing unless explicitly intended and documented.

## 10) Quick commands (copy/paste)

```bash
# tests
python -m unittest discover -v

# coverage task equivalent (if desired)
python -m pip install -U coverage
python -m coverage run -m unittest discover -s tests
python -m coverage lcov
```
