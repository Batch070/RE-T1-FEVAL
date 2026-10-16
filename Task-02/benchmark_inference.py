
"""Benchmark GCC-PHAT latency and memory usage."""

import csv
import json
import statistics
import time
import tracemalloc
from pathlib import Path

import numpy as np
import psutil

from tdoa_estimator import gcc_phat, make_delayed_signals


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def main():
    signal, reference, fs = make_delayed_signals(
        delay_samples=24, sample_rate=48000, size=4096
    )

    # Warm-up run: exclude initial setup effects from measurements.
    gcc_phat(signal, reference, fs, max_tau=0.01)

    process = psutil.Process()
    rss_before = process.memory_info().rss
    latencies_ms = []

    tracemalloc.start()
    for _ in range(100):
        start = time.perf_counter()
        result = gcc_phat(
            signal, reference, fs, max_tau=0.01
        )
        latencies_ms.append((time.perf_counter() - start) * 1000)

    _, peak_traced_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    rss_after = process.memory_info().rss

    summary = {
        "iterations": len(latencies_ms),
        "sample_rate_hz": fs,
        "signal_length": len(signal),
        "expected_delay_seconds": 24 / fs,
        "estimated_delay_seconds": result["delay_seconds"],
        "latency_mean_ms": statistics.mean(latencies_ms),
        "latency_median_ms": statistics.median(latencies_ms),
        "latency_max_ms": max(latencies_ms),
        "latency_min_ms": min(latencies_ms),
        "peak_traced_memory_kb": peak_traced_bytes / 1024,
        "rss_before_kb": rss_before / 1024,
        "rss_after_kb": rss_after / 1024,
        "rss_change_kb": (rss_after - rss_before) / 1024,
    }

    with (RESULTS / "task02_benchmark.json").open("w") as f:
        json.dump(summary, f, indent=2)

    with (RESULTS / "task02_latency.csv").open(
        "w", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(["iteration", "latency_ms"])
        for i, latency in enumerate(latencies_ms, start=1):
            writer.writerow([i, latency])

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
