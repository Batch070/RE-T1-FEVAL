
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "Task-01"
    / "timestamp_alignment.py"
)

spec = importlib.util.spec_from_file_location(
    "timestamp_alignment", MODULE_PATH
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

recover = module.recover_three_packet_gap
align = module.align_numeric_stream


class Task1Tests(unittest.TestCase):
    def test_three_packet_recovery(self):
        packets = [
            {
                "sensor": "IMU",
                "sequence": 0,
                "timestamp": 0.0,
                "measurements": {"x": 0.0},
            },
            {
                "sensor": "IMU",
                "sequence": 4,
                "timestamp": 0.04,
                "measurements": {"x": 4.0},
            },
        ]

        result = recover(packets)

        self.assertEqual(
            [p["sequence"] for p in result],
            [0, 1, 2, 3, 4],
        )
        self.assertEqual(
            [result[i]["measurements"]["x"] for i in (1, 2, 3)],
            [1.0, 2.0, 3.0],
        )
        self.assertTrue(
            all(result[i]["estimated"] for i in (1, 2, 3))
        )

    def test_timestamp_alignment(self):
        packets = [
            {
                "timestamp": 0.0,
                "measurements": {"x": 0.0},
            },
            {
                "timestamp": 2.0,
                "measurements": {"x": 10.0},
            },
        ]

        result = align(packets, [0.0, 1.0, 2.0])

        self.assertEqual(
            [r["measurements"]["x"] for r in result],
            [0.0, 5.0, 10.0],
        )
        self.assertTrue(result[1]["estimated"])
        self.assertFalse(result[0]["estimated"])
        self.assertFalse(result[2]["estimated"])


if __name__ == "__main__":
    unittest.main()
