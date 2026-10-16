
import csv
import importlib.util
import json
import logging
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "Task-01"

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

ingestion = load_module(
    "sensor_ingestion", TASK_DIR / "sensor_ingestion.py"
)
alignment = load_module(
    "timestamp_alignment", TASK_DIR / "timestamp_alignment.py"
)

(ROOT / "results").mkdir(exist_ok=True)
(ROOT / "logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(ROOT / "logs" / "challenge.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("task01")


def main():
    streams = {
        name: ingestion.generate_sensor_stream(name, seed=42 + i)
        for i, name in enumerate(("IMU", "Acoustic", "GPS"))
    }

    # Simulate three consecutive missing IMU packets.
    original_imu = streams["IMU"]
    received_imu = [
        packet for packet in original_imu
        if packet["sequence"] not in {20, 21, 22}
    ]

    recovered_imu = alignment.recover_three_packet_gap(received_imu)

    assert len(recovered_imu) == len(original_imu)
    assert [p["sequence"] for p in recovered_imu] == list(range(100))
    assert all(
        p.get("estimated", False)
        for p in recovered_imu
        if p["sequence"] in {20, 21, 22}
    )

    # Important: use the recovered stream for the next stage.
    streams["IMU"] = recovered_imu
    logger.info("Successfully recovered three missing IMU packets")

    # Create a common timeline across all three sensors.
    start = max(s[0]["timestamp"] for s in streams.values())
    end = min(s[-1]["timestamp"] for s in streams.values())
    target_times = np.arange(start, end, 0.02)

    aligned = {
        name: alignment.align_numeric_stream(stream, target_times)
        for name, stream in streams.items()
    }

    csv_path = ROOT / "results" / "sensor_alignment.csv"
    with csv_path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "timestamp", "sensor", "measurements_json", "estimated"
        ])
        for name, rows in aligned.items():
            for row in rows:
                writer.writerow([
                    row["timestamp"],
                    name,
                    json.dumps(row["measurements"]),
                    row["estimated"],
                ])

    summary = {
        "streams": {name: len(s) for name, s in streams.items()},
        "imu_packets_recovered": 3,
        "alignment_rows": {
            name: len(rows) for name, rows in aligned.items()
        },
        "results_file": "results/sensor_alignment.csv",
    }

    with (ROOT / "results" / "task01_summary.json").open("w") as file:
        json.dump(summary, file, indent=2)

    logger.info("Task 1 integration completed")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, AssertionError, ImportError, KeyError):
        logger.exception("Task 1 execution failed")
        raise
