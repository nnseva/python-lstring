"""
Benchmark: compare str.find and L.find on a very large string with a small fragment
near the middle.

Usage: run inside the project environment where the extension is installed (or `PYTHONPATH=.`):
    python benchmarks/bench_find.py

The script will print median timings for multiple runs.
"""

import time
import statistics
import argparse

from lstring import L


def build_test_strings(total_len=10_000_000, fragment="needle", filler="qwertyuiop"):
    # Compute how many filler characters to place on the left and right of fragment.
    frag_len = len(fragment)
    if frag_len > total_len:
        raise ValueError("fragment length must be <= total_len")

    # number of filler characters to place before fragment
    left_len = (total_len - frag_len) // 2
    # remainder goes to the right side to make total length exact
    right_len = total_len - frag_len - left_len

    # Build left and right using filler of arbitrary length
    if filler == "":
        raise ValueError("filler must be non-empty")
    flen = len(filler)

    # ensure we have enough repeats then slice to exact character count
    def build_side(n):
        if n <= 0:
            return ""
        repeats = (n // flen) + 1
        return (filler * repeats)[:n]

    left = build_side(left_len)
    right = build_side(right_len)

    data = left + fragment + right

    # return both Python str and L wrapping the same content
    py = data
    lz = L(py)
    pos = left_len
    return py, lz, py[pos:pos+frag_len]


def time_find(py, lz, sub, runs=5):
    py_times = []
    lz_fast_times = []
    lz_sliced_times = []

    # prepare a sliced L needle and a sliced haystack
    sliced_needle = L(sub)[:]
    sliced_hay = lz[:]

    for _ in range(runs):
        # pure Python str.find
        t0 = time.perf_counter()
        i = py.find(sub)
        t1 = time.perf_counter()
        py_times.append(t1 - t0)

        # fast-path: L haystack with plain Python str needle (both str-backed buffers)
        t0 = time.perf_counter()
        j = lz.find(sub)
        t1 = time.perf_counter()
        lz_fast_times.append(t1 - t0)

        # sliced needle (or sliced haystack) - this should bypass fast-path
        t0 = time.perf_counter()
        k = sliced_hay.find(sliced_needle)
        t1 = time.perf_counter()
        lz_sliced_times.append(t1 - t0)

        # sanity checks
        if i != j or i != k:
            raise RuntimeError(f"Mismatch: str.find -> {i}, L.find fast -> {j}, sliced -> {k}")

    return py_times, lz_fast_times, lz_sliced_times


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=int, default=10_000_000,
                        help='total size of the test string in bytes')
    parser.add_argument('--filler', type=str, default='qwertyuiop',
                        help='filler string to use for building the large string')
    parser.add_argument('--fragment', type=str, default='needle',
                        help='fragment string to insert into the large string and search for')
    parser.add_argument('--runs', type=int, default=7,
                        help='number of runs to average')
    args = parser.parse_args()

    print(f"Building test strings of size {args.size}...")
    py, lz, sub = build_test_strings(total_len=args.size, fragment=args.fragment, filler=args.filler)
    print("Built. Running benchmarks...")

    py_times, lz_fast_times, lz_sliced_times = time_find(py, lz, sub, runs=args.runs)

    def stats(times):
        return statistics.median(times), min(times), max(times)

    p_med, p_min, p_max = stats(py_times)
    f_med, f_min, f_max = stats(lz_fast_times)
    s_med, s_min, s_max = stats(lz_sliced_times)

    print("Results (seconds, median/min/max):")
    print(f"str.find:      {p_med:.6f} / {p_min:.6f} / {p_max:.6f}")
    print(f"L.find fast:   {f_med:.6f} / {f_min:.6f} / {f_max:.6f}")
    print(f"L.find sliced: {s_med:.6f} / {s_min:.6f} / {s_max:.6f}")

    print("Per-run details (str.find):", ", ".join(f"{t:.6f}" for t in py_times))
    print("Per-run details (L.find fast):", ", ".join(f"{t:.6f}" for t in lz_fast_times))
    print("Per-run details (L.find sliced):", ", ".join(f"{t:.6f}" for t in lz_sliced_times))


if __name__ == '__main__':
    main()
