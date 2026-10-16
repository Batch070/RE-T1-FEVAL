
"""Automated tests for Task 3 logging and exception handling."""

import importlib.util
import logging
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "Task-03" / "monitoring.py"

spec = importlib.util.spec_from_file_location("monitoring", MODULE_PATH)
monitoring = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitoring)


class Task3Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger("task03_test")
        cls.logger.setLevel(logging.INFO)
        cls.logger.handlers.clear()
        cls.logger.addHandler(logging.NullHandler())

    def test_valid_packet(self):
        packet = {
            "sensor": "IMU",
            "sequence": 1,
            "timestamp": 0.02,
            "measurements": {"accel_x": 0.1},
        }
        self.assertTrue(monitoring.process_packet(packet, self.logger))

    def test_unknown_sensor_rejected(self):
        packet = {
            "sensor": "UNKNOWN",
            "sequence": 2,
            "timestamp": 0.04,
            "measurements": {"value": 1.0},
        }
        self.assertFalse(monitoring.process_packet(packet, self.logger))

    def test_missing_measurements_rejected(self):
        packet = {
            "sensor": "GPS",
            "sequence": 3,
            "timestamp": 0.06,
            "measurements": {},
        }
        self.assertFalse(monitoring.process_packet(packet, self.logger))

    def test_non_dictionary_packet_rejected(self):
        self.assertFalse(monitoring.process_packet("invalid", self.logger))


if __name__ == "__main__":
    unittest.main()
