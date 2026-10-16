
"""Automated tests for the GCC-PHAT TDoA estimator."""

import importlib.util
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "Task-02" / "tdoa_estimator.py"

spec = importlib.util.spec_from_file_location("tdoa_estimator", MODULE_PATH)
tdoa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tdoa)


class TDoATests(unittest.TestCase):

    def test_known_delays(self):
        sample_rate = 48000

        for delay_samples in (6, 12, 24, 48):
            with self.subTest(delay_samples=delay_samples):
                signal, reference, fs = tdoa.make_delayed_signals(
                    delay_samples=delay_samples,
                    sample_rate=sample_rate,
                    size=4096,
                    seed=42,
                )

                result = tdoa.gcc_phat(
                    signal, reference, fs,
                    max_tau=0.01,
                    interp=16,
                )

                expected = delay_samples / sample_rate
                self.assertAlmostEqual(
                    result["delay_seconds"], expected,
                    delta=1 / (16 * sample_rate),
                )

    def test_rejects_non_1d_input(self):
        with self.assertRaises(ValueError):
            tdoa.gcc_phat(
                np.ones((2, 4)), np.ones(8), 48000
            )

    def test_rejects_non_finite_input(self):
        signal = np.ones(16)
        signal[3] = np.nan

        with self.assertRaises(ValueError):
            tdoa.gcc_phat(signal, np.ones(16), 48000)

    def test_rejects_invalid_sample_rate(self):
        with self.assertRaises(ValueError):
            tdoa.gcc_phat(np.ones(16), np.ones(16), 0)

    def test_rejects_too_short_signals(self):
        with self.assertRaises(ValueError):
            tdoa.gcc_phat(np.array([1.0]), np.array([1.0]), 48000)


if __name__ == "__main__":
    unittest.main()
