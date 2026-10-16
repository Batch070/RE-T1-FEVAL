
"""Structured logging and exception handling utilities."""

import json
import logging
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class JsonFormatter(logging.Formatter):
    """Format log records as one JSON object per line."""

    def format(self, record):
        entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in ("task", "sensor", "sequence", "latency_ms", "event"):
            if hasattr(record, key):
                entry[key] = getattr(record, key)

        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry)


def configure_logging():
    logger = logging.getLogger("embedded_ai")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    handler = logging.FileHandler(
        LOG_DIR / "structured.log", encoding="utf-8"
    )
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(console)

    return logger


def process_packet(packet, logger):
    """Validate a sensor packet and log processing latency."""
    start = time.perf_counter()

    try:
        if not isinstance(packet, dict):
            raise TypeError("Packet must be a dictionary")

        sensor = packet.get("sensor")
        sequence = packet.get("sequence")
        timestamp = packet.get("timestamp")
        measurements = packet.get("measurements")

        if sensor not in {"IMU", "Acoustic", "GPS"}:
            raise ValueError("Unknown sensor type")
        if not isinstance(sequence, int) or sequence < 0:
            raise ValueError("Sequence must be a non-negative integer")
        if not isinstance(timestamp, (int, float)) or timestamp < 0:
            raise ValueError("Timestamp must be non-negative")
        if not isinstance(measurements, dict) or not measurements:
            raise ValueError("Measurements must be a non-empty dictionary")

        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Packet validated",
            extra={
                "task": "Task-03",
                "sensor": sensor,
                "sequence": sequence,
                "latency_ms": round(latency_ms, 4),
                "event": "packet_validated",
            },
        )
        return True

    except (TypeError, ValueError, AttributeError):
        logger.exception(
            "Packet processing failed",
            extra={"task": "Task-03", "event": "packet_error"},
        )
        return False


if __name__ == "__main__":
    log = configure_logging()

    valid_packet = {
        "sensor": "IMU",
        "sequence": 1,
        "timestamp": 0.02,
        "measurements": {"accel_x": 0.1, "accel_y": 0.2},
    }

    invalid_packet = {
        "sensor": "UNKNOWN",
        "sequence": 2,
        "timestamp": 0.04,
        "measurements": {"value": 1.0},
    }

    assert process_packet(valid_packet, log)
    assert not process_packet(invalid_packet, log)

    print("Task 3 logging and error-handling demo completed.")
    print("Structured log: logs/structured.log")
