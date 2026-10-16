
"""Generate reproducible asynchronous synthetic sensor streams."""

import random


def generate_sensor_stream(
    sensor: str,
    count: int = 100,
    interval_s: float = 0.1,
    seed: int = 42,
) -> list[dict]:
    if count < 2:
        raise ValueError("count must be at least 2")
    if interval_s <= 0.06:
        raise ValueError("interval_s must exceed 60 ms")

    rng = random.Random(seed)

    packets = []
    sensor_offset = {
        "IMU": 0.0,
        "Acoustic": 0.02,
        "GPS": 0.04,
    }

    for i in range(count):
        timestamp = (
            sensor_offset.get(sensor, 0.0)
            + i * interval_s
            + rng.uniform(0.010, 0.050)
        )

        if sensor == "IMU":
            values = {
                "accel_x": rng.uniform(-1, 1),
                "accel_y": rng.uniform(-1, 1),
                "accel_z": rng.uniform(9, 10),
                "gyro_x": rng.uniform(-0.1, 0.1),
                "gyro_y": rng.uniform(-0.1, 0.1),
                "gyro_z": rng.uniform(-0.1, 0.1),
            }
        elif sensor == "Acoustic":
            values = {"amplitude": rng.uniform(-1, 1)}
        elif sensor == "GPS":
            values = {
                "latitude": 31 + rng.uniform(-0.001, 0.001),
                "longitude": 76 + rng.uniform(-0.001, 0.001),
                "altitude_m": rng.uniform(300, 500),
            }
        else:
            raise ValueError(f"Unsupported sensor: {sensor}")

        packets.append({
            "sensor": sensor,
            "sequence": i,
            "timestamp": round(timestamp, 6),
            "measurements": values,
            "estimated": False,
        })

    return packets


if __name__ == "__main__":
    for name in ("IMU", "Acoustic", "GPS"):
        stream = generate_sensor_stream(name)
        assert all(
            stream[i]["timestamp"] < stream[i + 1]["timestamp"]
            for i in range(len(stream) - 1)
        )
        print(
            f"{name}: {len(stream)} packets, "
            f"first sequence={stream[0]['sequence']}"
        )
