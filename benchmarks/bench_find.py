"""
Benchmark: compare str.find and _lstr.find on a very large string with a small fragment
near the middle.

Usage: run inside the project environment where the extension is installed (or `PYTHONPATH=.`):
    python benchmarks/bench_find.py

The script will print median timings for multiple runs.
"""

import time
import statistics
import argparse

from lstring import _lstr


def build_test_strings(total_len=10_000_000, fragment=b"needle"):
    # base chunk to repeat (ascii safe)
    chunk = b"a" * 1024
    # compute repeats to get near total_len
    repeats = total_len // len(chunk)
    data = chunk * repeats

    # place fragment near the middle
    mid = len(data) // 2
    pos = mid - len(fragment) // 2
    data = data[:pos] + fragment + data[pos+len(fragment):]

    # return both Python str and _lstr wrapping the same content
    py = data.decode('ascii')
    lz = _lstr(py)
    return py, lz, py[pos:pos+len(fragment)]


def time_find(py, lz, sub, runs=5):
    py_times = []
    lz_times = []

    for _ in range(runs):
        t0 = time.perf_counter()
        i = py.find(sub)
        t1 = time.perf_counter()
        py_times.append(t1 - t0)

        t0 = time.perf_counter()
        j = lz.find(sub)
        t1 = time.perf_counter()
        lz_times.append(t1 - t0)

        if i != j:
            raise RuntimeError(f"Mismatch: str.find -> {i}, _lstr.find -> {j}")

    return py_times, lz_times


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=int, default=10_000_000,
                        help='total size of the test string in bytes')
    parser.add_argument('--runs', type=int, default=7,
                        help='number of runs to average')
    args = parser.parse_args()

    print(f"Building test strings of size {args.size}...")
    py, lz, sub = build_test_strings(total_len=args.size, fragment=b"needle")
    print("Built. Running benchmarks...")

    py_times, lz_times = time_find(py, lz, sub, runs=args.runs)

    def stats(times):
        return statistics.median(times), min(times), max(times)

    p_med, p_min, p_max = stats(py_times)
    l_med, l_min, l_max = stats(lz_times)

    print("Results (seconds, median/min/max):")
    print(f"str.find: {p_med:.6f} / {p_min:.6f} / {p_max:.6f}")
    print(f"_lstr.find: {l_med:.6f} / {l_min:.6f} / {l_max:.6f}")

    print("Per-run details (str.find):", ", ".join(f"{t:.6f}" for t in py_times))
    print("Per-run details (_lstr.find):", ", ".join(f"{t:.6f}" for t in lz_times))


if __name__ == '__main__':
    main()
