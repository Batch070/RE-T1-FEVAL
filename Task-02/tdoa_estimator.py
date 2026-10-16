
"""GCC-PHAT acoustic time-difference-of-arrival estimator."""

import numpy as np


def gcc_phat(signal, reference, sample_rate, max_tau=None, interp=16):
    """Estimate the delay of signal relative to reference, in seconds."""
    signal = np.asarray(signal, dtype=np.float64)
    reference = np.asarray(reference, dtype=np.float64)

    if signal.ndim != 1 or reference.ndim != 1:
        raise ValueError("Signals must be one-dimensional")
    if len(signal) < 2 or len(reference) < 2:
        raise ValueError("Signals must contain at least two samples")
    if not np.all(np.isfinite(signal)) or not np.all(np.isfinite(reference)):
        raise ValueError("Signals must contain only finite values")
    if sample_rate <= 0 or interp < 1:
        raise ValueError("sample_rate and interp must be positive")
    if max_tau is not None and max_tau <= 0:
        raise ValueError("max_tau must be positive")

    # Remove DC offsets.
    signal = signal - np.mean(signal)
    reference = reference - np.mean(reference)

    n = len(signal) + len(reference)
    signal_fft = np.fft.rfft(signal, n=n)
    reference_fft = np.fft.rfft(reference, n=n)

    cross_spectrum = signal_fft * np.conj(reference_fft)
    magnitude = np.abs(cross_spectrum)
    cross_spectrum /= np.maximum(magnitude, 1e-12)

    correlation = np.fft.irfft(
        cross_spectrum, n=interp * n
    )

    max_shift = interp * n // 2
    if max_tau is not None:
        max_shift = min(
            max_shift, int(interp * sample_rate * max_tau)
        )

    if max_shift < 1:
        raise ValueError("Search window is too small")

    correlation = np.concatenate((
        correlation[-max_shift:],
        correlation[:max_shift + 1],
    ))

    shift = int(np.argmax(np.abs(correlation)) - max_shift)
    delay_seconds = shift / (interp * sample_rate)

    return {
        "delay_seconds": float(delay_seconds),
        "delay_samples": float(shift / interp),
        "sample_rate": int(sample_rate),
        "interpolation": int(interp),
    }


def make_delayed_signals(delay_samples=24, sample_rate=48000, size=4096,
                         seed=42):
    """Create reproducible synthetic signals with a known delay."""
    if delay_samples < 0 or delay_samples >= size // 2:
        raise ValueError("delay_samples must be in [0, size // 2)")

    rng = np.random.default_rng(seed)
    reference = rng.normal(size=size)
    signal = np.zeros(size, dtype=np.float64)
    signal[delay_samples:] = reference[:-delay_samples] if delay_samples else reference

    # Add small independent noise to simulate imperfect measurements.
    signal += rng.normal(scale=0.01, size=size)

    return signal, reference, sample_rate


if __name__ == "__main__":
    signal, reference, fs = make_delayed_signals(delay_samples=24)
    result = gcc_phat(
        signal, reference, fs, max_tau=0.01, interp=16
    )
    print("Expected delay (seconds):", 24 / fs)
    print("Estimated delay:", result["delay_seconds"])
    print("Estimated samples:", result["delay_samples"])
