
"""Timestamp alignment and missing-packet recovery."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def recover_three_packet_gap(packets):
    """Recover up to 3 missing sequence numbers between valid packets."""
    if not packets:
        raise ValueError("Packets cannot be empty")

    ordered = sorted(packets, key=lambda p: p["sequence"])

    if len({p["sequence"] for p in ordered}) != len(ordered):
        raise ValueError("Duplicate sequence numbers detected")

    recovered = []

    for left, right in zip(ordered, ordered[1:]):
        recovered.append(left)

        gap = right["sequence"] - left["sequence"] - 1

        if gap <= 0:
            continue

        if gap > 3:
            logger.warning("Gap of %d packets exceeds recovery limit", gap)
            continue

        t0, t1 = left["timestamp"], right["timestamp"]

        if t1 <= t0:
            raise ValueError("Timestamps must increase")

        left_values = left["measurements"]
        right_values = right["measurements"]

        if left_values.keys() != right_values.keys():
            raise ValueError("Measurement fields do not match")

        for step in range(1, gap + 1):
            ratio = step / (gap + 1)

            values = {
                key: float(left_values[key]) + ratio * (
                    float(right_values[key]) - float(left_values[key])
                )
                for key in left_values
            }

            recovered.append({
                "sensor": left["sensor"],
                "sequence": left["sequence"] + step,
                "timestamp": t0 + ratio * (t1 - t0),
                "measurements": values,
                "estimated": True,
            })

            logger.info(
                "Recovered %s packet sequence=%d",
                left["sensor"],
                left["sequence"] + step,
            )

    recovered.append(ordered[-1])

    return sorted(recovered, key=lambda p: p["sequence"])


def align_numeric_stream(packets, target_times):
    """Interpolate numeric measurements onto a common time grid."""
    if not packets:
        raise ValueError("Cannot align an empty stream")

    packets = sorted(packets, key=lambda p: p["timestamp"])
    times = np.asarray(
        [p["timestamp"] for p in packets], dtype=float
    )
    target_times = np.asarray(target_times, dtype=float)

    if not np.all(np.isfinite(times)) or not np.all(
        np.isfinite(target_times)
    ):
        raise ValueError("Timestamps must be finite")

    if np.any(np.diff(times) <= 0):
        raise ValueError("Source timestamps must be strictly increasing")

    keys = packets[0]["measurements"].keys()

    if any(p["measurements"].keys() != keys for p in packets):
        raise ValueError("Measurement fields do not match")

    output = []

    for target in target_times:
        inside_range = times[0] <= target <= times[-1]

        row = {
            "timestamp": float(target),
            "measurements": None,
            "estimated": True,
        }

        if inside_range:
            row["measurements"] = {
                key: float(np.interp(
                    target,
                    times,
                    [p["measurements"][key] for p in packets],
                ))
                for key in keys
            }

            row["estimated"] = not bool(
                np.any(np.isclose(times, target, atol=1e-9))
            )

        output.append(row)

    return output

