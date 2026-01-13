"""Benchmark: L.findcs performance across different L buffer shapes and charset sizes.

This script does NOT modify the core implementation; it only exercises the public Python API.

Usage (from repo root, with extension importable):
    python benchmarks/bench_findcs.py

It writes a timestamped JSON report under benchmarks/results/.
"""

import argparse
from dataclasses import dataclass
import json
import os
import platform
import statistics
import subprocess
import time
import timeit
from datetime import datetime, timezone

import lstring
from lstring import L


def _latin1_charset_excluding(exclude: int) -> str:
    # Build 0..255 as latin-1 string, excluding one byte.
    b = bytes([i for i in range(256) if i != exclude])
    return b.decode("latin1")


def _make_charset(size: int, *, exclude_byte: int, include_byte: int) -> str:
    """Create a charset string of requested size.

    - Ensures `exclude_byte` is not present (so filler does not match early).
    - Ensures `include_byte` IS present (so we have a known match).

    For size > 255, we append Unicode code points > 255; those won't match UCS1
    haystacks but still stress membership checks.
    """

    if size <= 0:
        return ""

    base = _latin1_charset_excluding(exclude_byte)

    # Ensure include_byte is in the base set; if it's excluded by mistake, fix.
    include_char = bytes([include_byte]).decode("latin1")
    if include_char not in base:
        base = include_char + base

    if size <= len(base):
        # Put include_char at the end to make the successful match maximally expensive.
        trimmed = base.replace(include_char, "")
        return (trimmed[: size - 1] + include_char) if size > 1 else include_char

    # Need more than 255 characters: append higher code points.
    # Still keep include_char at the end.
    remaining = size - 1
    chars = [c for c in base if c != include_char]
    out = chars[: min(remaining, len(chars))]
    remaining -= len(out)

    # Append U+0100 .. as needed.
    if remaining > 0:
        out.extend(chr(0x0100 + i) for i in range(remaining))

    out.append(include_char)
    return "".join(out)


def _build_haystack_str(total_len: int, *, filler_byte: int, target_byte: int) -> str:
    if total_len <= 0:
        return ""
    if total_len == 1:
        return bytes([target_byte]).decode("latin1")
    return (bytes([filler_byte]) * (total_len - 1) + bytes([target_byte])).decode("latin1")


def _build_scenarios_from_base(base: str) -> dict[str, L]:
    total_len = len(base)
    if total_len == 0:
        return {
            "simple": L(base),
            "slice": L(base),
            "concat": L(base),
            "join": L(base),
            "mul_slice": L(base),
        }

    filler_char = base[0]
    target_char = base[-1]

    # 1) Simple: direct str-backed buffer.
    simple = L(base)

    # 2) Slice: slice view over a larger base.
    prefix = "p" * 10
    suffix = "s" * 10
    sliced = L(prefix + base + suffix)[len(prefix) : len(prefix) + total_len]

    # 3) Concat: concatenation tree.
    left_len = total_len // 2
    right_len = total_len - left_len
    right = (filler_char * max(0, right_len - 1)) + target_char
    concat = L(filler_char * left_len) + L(right)

    # 4) Join: build from many chunks.
    # Make chunks that sum to total_len, with target in the last chunk.
    chunk = filler_char * 32
    chunks = []
    remaining = total_len
    while remaining > 0:
        take = min(len(chunk), remaining)
        chunks.append(chunk[:take])
        remaining -= take
    # Replace last char with target.
    if chunks:
        last = chunks[-1]
        if not last:
            chunks[-1] = target_char
        else:
            chunks[-1] = last[:-1] + target_char
    joined = L("|").join(chunks)

    # 5) Mul+slice: repetition + slicing (note: may yield early matches).
    mul_base = L(filler_char * 97 + target_char) * max(1, (total_len // 98) + 1)
    mul_slice = mul_base[:total_len]

    return {
        "simple": simple,
        "slice": sliced,
        "concat": concat,
        "join": joined,
        "mul_slice": mul_slice,
    }


def _choose_number(total_len: int, charset_size: int) -> int:
    # Heuristic: target ~5M inner comparisons per timing batch.
    approx = max(1, total_len) * max(1, charset_size)
    target = 5_000_000
    n = max(1, target // approx)
    return int(min(n, 2000))


def _bench_findcs(lz: L, charset: object, *, repeats: int, number: int) -> dict:
    fn = lz.findcs

    # Sanity: compute expected result once via a Python baseline.
    # We don't assume where the match is (some scenarios may have early matches).
    hay_py = str(lz)
    charset_py = str(charset) if isinstance(charset, L) else str(charset)
    if charset_py == "":
        expected = -1
    else:
        cs = set(charset_py)
        expected = -1
        for i, ch in enumerate(hay_py):
            if ch in cs:
                expected = i
                break

    got = fn(charset)
    if got != expected:
        raise RuntimeError(f"Unexpected findcs result: got={got}, expected={expected}")

    def stmt():
        return fn(charset)

    times = timeit.repeat(stmt, number=number, repeat=repeats)
    per_call = [t / number for t in times]
    return {
        "repeats": repeats,
        "number": number,
        "median_s": statistics.median(per_call),
        "min_s": min(per_call),
        "max_s": max(per_call),
        "runs_s": per_call,
    }


def _unicode_kind_guess(s: str) -> str:
    if not s:
        return "empty"
    max_ord = max(ord(ch) for ch in s)
    if max_ord <= 0xFF:
        return "ucs1"
    if max_ord <= 0xFFFF:
        return "ucs2"
    return "ucs4"


def _dense_charset(size: int, *, start_cp: int, exclude_cp: int, include_cp: int) -> str:
    if size <= 0:
        return ""
    out: list[str] = []
    cp = start_cp

    include_ch = chr(include_cp)
    exclude_ch = chr(exclude_cp)

    # Collect size-1 chars (excluding include/exclude), then append include_ch.
    while len(out) < max(0, size - 1):
        ch = chr(cp)
        if ch != exclude_ch and ch != include_ch:
            out.append(ch)
        cp += 1
        if cp > 0x10FFFF:
            raise ValueError("dense charset range exceeded Unicode max")

    return ("".join(out) + include_ch) if size > 1 else include_ch


def _sparse_charset(size: int, *, start_cp: int, step: int, exclude_cp: int, include_cp: int) -> str:
    if size <= 0:
        return ""
    if step <= 256:
        raise ValueError("sparse charset step must be > 256")

    include_ch = chr(include_cp)
    exclude_ch = chr(exclude_cp)
    out: list[str] = []

    # Fill size-1 sparse points.
    cp = start_cp
    while len(out) < max(0, size - 1):
        if cp > 0x10FFFF:
            cp = (cp % 0x10FFFF) + 1
        ch = chr(cp)
        if ch != exclude_ch and ch != include_ch:
            out.append(ch)
        cp += step

    return ("".join(out) + include_ch) if size > 1 else include_ch


def _multi_range_sparse_charset(size: int, *, ranges: list[tuple[int, int]], step: int, exclude_cp: int, include_cp: int) -> str:
    """Build a sparse charset by cycling through multiple distant ranges.

    This is meant to create very non-local codepoints (gaps > 256) and multiple
    disjoint bands, without trying to find an optimal packing.
    """
    if size <= 0:
        return ""
    if step <= 256:
        raise ValueError("multi-range sparse charset step must be > 256")
    if not ranges:
        raise ValueError("ranges must be non-empty")

    include_ch = chr(include_cp)
    exclude_ch = chr(exclude_cp)
    out: list[str] = []

    # Maintain independent cursors per range.
    cursors = [start for start, _end in ranges]

    r = 0
    while len(out) < max(0, size - 1):
        start, end = ranges[r]
        cp = cursors[r]
        if cp < start or cp >= end:
            cp = start
        ch = chr(cp)
        if ch != exclude_ch and ch != include_ch:
            out.append(ch)
        cursors[r] = cp + step
        r = (r + 1) % len(ranges)

    return ("".join(out) + include_ch) if size > 1 else include_ch


@dataclass(frozen=True)
class CharsetCase:
    name: str
    filler: str
    target: str
    charset_builder: callable

    def build_haystack(self, total_len: int) -> str:
        if total_len <= 0:
            return ""
        if total_len == 1:
            return self.target
        return (self.filler * (total_len - 1)) + self.target

    def build_charset(self, size: int) -> str:
        return self.charset_builder(size, exclude_cp=ord(self.filler), include_cp=ord(self.target))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--length", type=int, default=50_000, help="haystack length")
    parser.add_argument(
        "--sizes",
        type=str,
        default="1,4,16,64,256,512",
        help="comma-separated charset sizes",
    )
    parser.add_argument("--repeats", type=int, default=7, help="timeit repeats")
    parser.add_argument(
        "--out",
        type=str,
        default="",
        help="output JSON path (default: benchmarks/results/findcs_<timestamp>.json)",
    )
    args = parser.parse_args()

    # Keep lazy structures stable.
    orig_thresh = lstring.get_optimize_threshold()
    lstring.set_optimize_threshold(0)

    try:
        total_len = int(args.length)
        sizes = [int(x) for x in args.sizes.split(",") if x.strip()]

        cases = [
            # UCS1
            CharsetCase(
                name="latin1_dense",
                filler="x",
                target="y",
                charset_builder=lambda size, exclude_cp, include_cp: _make_charset(
                    size,
                    exclude_byte=exclude_cp,
                    include_byte=include_cp,
                ),
            ),
            # UCS2 (BMP)
            CharsetCase(
                name="ucs2_cyrillic_dense",
                filler="Ж",  # U+0416
                target="Я",  # U+042F
                charset_builder=lambda size, exclude_cp, include_cp: _dense_charset(
                    size,
                    start_cp=0x0400,
                    exclude_cp=exclude_cp,
                    include_cp=include_cp,
                ),
            ),
            CharsetCase(
                name="ucs2_sparse_step512",
                filler="Ā",  # U+0100
                target="ő",  # U+0151
                charset_builder=lambda size, exclude_cp, include_cp: _sparse_charset(
                    size,
                    start_cp=0x0100,
                    step=512,
                    exclude_cp=exclude_cp,
                    include_cp=include_cp,
                ),
            ),
            # UCS4
            CharsetCase(
                name="ucs4_emoji_dense",
                filler="😀",  # U+1F600
                target="😺",  # U+1F63A
                charset_builder=lambda size, exclude_cp, include_cp: _dense_charset(
                    size,
                    start_cp=0x1F600,
                    exclude_cp=exclude_cp,
                    include_cp=include_cp,
                ),
            ),
            CharsetCase(
                name="ucs4_sparse_step1024",
                filler="🌀",  # U+1F300
                target="🧠",  # U+1F9E0
                charset_builder=lambda size, exclude_cp, include_cp: _sparse_charset(
                    size,
                    start_cp=0x1F300,
                    step=1024,
                    exclude_cp=exclude_cp,
                    include_cp=include_cp,
                ),
            ),
            # Multi-range sparse: mix very distant blocks (BMP + SMP), gaps > 256.
            CharsetCase(
                name="multi_range_sparse",
                filler="x",
                target="🧠",  # U+1F9E0
                charset_builder=lambda size, exclude_cp, include_cp: _multi_range_sparse_charset(
                    size,
                    ranges=[
                        (0x0400, 0x0500),   # Cyrillic
                        (0x2200, 0x2300),   # Mathematical Operators
                        (0x1F300, 0x1F400), # Misc Symbols and Pictographs
                        (0x1F900, 0x1FA00), # Supplemental Symbols and Pictographs
                    ],
                    step=769,
                    exclude_cp=exclude_cp,
                    include_cp=include_cp,
                ),
            ),
        ]

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = args.out or os.path.join("benchmarks", "results", f"findcs_{ts}.json")

        try:
            git_head = (
                subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
                .decode("ascii", errors="replace")
                .strip()
            )
        except Exception:
            git_head = None

        report = {
            "meta": {
                "timestamp_utc": ts,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "processor": platform.processor() or None,
                "git_head": git_head,
                "optimize_threshold": 0,
                "lstring_version": getattr(lstring, "__version__", None),
                "length": total_len,
                "charset_sizes": sizes,
                "cases": [c.name for c in cases],
            },
            "results": [],
        }

        for case in cases:
            haystack = case.build_haystack(total_len)
            scenarios = _build_scenarios_from_base(haystack)

            for charset_size in sizes:
                charset_str = case.build_charset(charset_size)
                charset_L = L(charset_str)

                for charset_type, charset_obj in (("str", charset_str), ("L", charset_L)):
                    for scenario_name, lz in scenarios.items():
                        number = _choose_number(total_len, charset_size)
                        stats = _bench_findcs(lz, charset_obj, repeats=args.repeats, number=number)
                        report["results"].append(
                            {
                                "case": case.name,
                                "haystack_kind": _unicode_kind_guess(haystack),
                                "charset_kind": _unicode_kind_guess(charset_str),
                                "scenario": scenario_name,
                                "charset_type": charset_type,
                                "charset_size": charset_size,
                                **stats,
                            }
                        )
                        print(
                            f"{case.name:18s} {scenario_name:10s} charset={charset_size:4d} ({charset_type}) "
                            f"median={stats['median_s'] * 1e6:9.1f} us/call"
                        )

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\nWrote: {out_path}")
        return 0

    finally:
        lstring.set_optimize_threshold(orig_thresh)


if __name__ == "__main__":
    raise SystemExit(main())
