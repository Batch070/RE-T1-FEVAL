# Embedded AI & Acoustic Sensing Challenge

**Multi-Sensor Data Ingestion | Fault Recovery | Acoustic TDoA | Performance Profiling | Structured Logging**

![Python](https://img.shields.io/badge/Python-3.14-blue)
![NumPy](https://img.shields.io/badge/NumPy-Scientific%20Computing-013243)
![Testing](https://img.shields.io/badge/Tests-11%20Passed-success)
![Status](https://img.shields.io/badge/Status-Implementation%20Complete-green)

## 1. Project Overview

This project implements an Embedded AI and Acoustic Sensing pipeline designed to demonstrate asynchronous sensor data processing, fault recovery, acoustic time-delay estimation, performance measurement, and robust error handling.

The system simulates three sensor streams:

- **IMU (Inertial Measurement Unit):** Simulated acceleration and gyroscope measurements.
- **Acoustic Sensor:** Simulated acoustic amplitude measurements.
- **GPS:** Simulated latitude, longitude, and altitude measurements.

The pipeline processes sensor packets with timestamps, handles missing packets, aligns numeric measurements to a common timeline, estimates acoustic time differences using GCC-PHAT, benchmarks execution performance, and records structured logs for debugging and monitoring.

> **Current scope:** The implementation and automated tests use synthetic data. Integration with physical sensors, real microphone recordings, and embedded hardware has not yet been validated.

---

## 2. Objectives

The main objectives of this project are:

1. Generate reproducible asynchronous sensor data.
2. Maintain packet sequence numbers and timestamps.
3. Recover up to three consecutive missing packets using interpolation.
4. Align sensor measurements on a shared time grid.
5. Estimate acoustic Time Difference of Arrival (TDoA) using GCC-PHAT.
6. Measure algorithm execution latency and memory usage.
7. Validate algorithms using automated unit tests.
8. Implement exception handling and structured logging.
9. Save processing results in CSV and JSON formats for analysis.

---

## 3. Project Tasks

### Task 1 — Asynchronous Sensor Ingestion and Fault Recovery

**Objective:** Process multiple sensor streams and recover a limited number of consecutive missing packets.

#### 3.1 Synthetic Sensor Generation

The sensor generator produces 100 packets for each of the following streams:

| Sensor | Simulated measurements |
|---|---|
| IMU | Acceleration and gyroscope values |
| Acoustic | Acoustic amplitude |
| GPS | Latitude, longitude, altitude |

Each packet contains a sensor identifier, sequence number, timestamp, and measurements.

Example packet:

```json
{
  "sensor": "IMU",
  "sequence": 0,
  "timestamp": 0.033478,
  "measurements": {
    "accel_x": 0.25,
    "accel_y": -0.18,
    "accel_z": 9.72
  },
  "estimated": false
}
```

*The values above illustrate the packet format; actual generated values depend on the random seed.*

#### 3.2 Timestamp Alignment

Sensor streams can have different timestamps. To compare their measurements, the pipeline creates a common timeline with a 20 ms interval.

Linear interpolation estimates numeric measurements between observed samples:

\[
x(t)=x_0+\frac{t-t_0}{t_1-t_0}(x_1-x_0)
\]

Where:

- \(t_0,t_1\) are adjacent observed timestamps.
- \(x_0,x_1\) are the corresponding measurements.
- \(t\) is the target timestamp.

The implementation uses NumPy interpolation for numeric measurements. Targets outside the observed time range are represented without extrapolating measurements.

#### 3.3 Missing Packet Recovery

The integration test simulates the loss of three consecutive IMU packets with sequence numbers 20, 21, and 22.

When a gap has valid packets on both sides, the recovery function interpolates missing timestamps and measurements using the surrounding packets.

For a missing value between two endpoints:

\[
x_k=x_a+\frac{k-a}{b-a}(x_b-x_a)
\]

Recovered packets are marked with `estimated: true`.

**Recovery policy:** The implementation is intended to reconstruct gaps of up to three missing packets when both endpoints are available. Larger gaps are not reconstructed by this recovery function.

#### 3.4 Task 1 Outputs

- `results/sensor_alignment.csv`
- `results/task01_summary.json`
- `logs/challenge.log`

The CSV stores timestamps, sensor identifiers, measurement data, and estimation flags. The JSON summary records stream counts, recovery count, and aligned row counts.

---

### Task 2 — Acoustic Time Difference of Arrival (TDoA)

**Objective:** Estimate the relative delay between two acoustic signals and profile the algorithm's performance.

#### 3.5 What Is TDoA?

Time Difference of Arrival is the difference between the times at which a sound reaches two sensors.

If the sound reaches microphone A before microphone B, the measured delay can help estimate the sound source's direction or location when combined with microphone geometry and additional measurements.

\[
\Delta t=t_B-t_A
\]

Where \(t_A\) and \(t_B\) are the signal arrival times at the two microphones.

#### 3.6 GCC-PHAT Algorithm

The implementation uses Generalized Cross-Correlation with Phase Transform (GCC-PHAT).

The high-level processing stages are:

1. Convert the signals into NumPy arrays.
2. Validate signal dimensions, finite values, and sampling parameters.
3. Remove the mean to reduce DC offsets.
4. Compute the Fourier transforms.
5. Calculate the cross-spectrum.
6. Normalize the cross-spectrum by its magnitude.
7. Compute the inverse Fourier transform to obtain the correlation function.
8. Search for the strongest correlation peak within the permitted delay window.
9. Convert the estimated sample shift into seconds.

The phase transform normalization is:

\[
R_{\mathrm{PHAT}}(f)=
\frac{X(f)Y^*(f)}
{|X(f)Y^*(f)|}
\]

A small denominator floor is used to avoid division by zero.

The estimated delay is calculated from the peak's sample shift:

\[
\hat{\tau}=\frac{\hat{k}}{f_s}
\]

Where:

- \(\hat{k}\) is the estimated shift in samples.
- \(f_s\) is the sampling frequency.
- \(\hat{\tau}\) is the estimated delay in seconds.

The implementation supports interpolation of the correlation function to improve delay resolution.

#### 3.7 Synthetic Delay Validation

The test signal generator creates a reproducible reference signal and a delayed version with a small amount of noise.

Current demonstration configuration:

| Parameter | Value |
|---|---:|
| Sampling frequency | 48,000 Hz |
| Signal length | 4,096 samples |
| Injected delay | 24 samples |
| Expected delay | 0.0005 seconds |
| Estimated delay in demonstration | 0.0005 seconds |

The known-delay tests validate several injected delays.

**Interpretation:** This confirms the estimator's behavior on the implemented synthetic examples. It does not establish accuracy for noisy real-world recordings, reverberant rooms, or actual microphone arrays.

#### 3.8 Performance Profiling

The benchmark executes the estimator 100 times after a warm-up run.

It records:

- Mean execution latency
- Median execution latency
- Minimum execution latency
- Maximum execution latency
- Peak Python-tracked memory allocation
- Process resident memory (RSS) before and after the benchmark

Latency is measured with Python's high-resolution performance timer. `tracemalloc` measures Python-tracked allocations, while `psutil` provides process RSS measurements.

#### 3.9 Example Benchmark Results

One recorded benchmark run produced the following results:

| Metric | Measured value |
|---|---:|
| Iterations | 100 |
| Mean latency | 3.21 ms |
| Median latency | 2.52 ms |
| Minimum latency | 2.46 ms |
| Maximum latency | 10.13 ms |
| Peak traced memory | 1,444 KB |
| RSS before benchmark | 39,180 KB |
| RSS after benchmark | 40,164 KB |
| RSS change | +984 KB |

Results vary with CPU load, runtime state, and environment. RSS change is a before-and-after process measurement, not the peak memory used exclusively by the algorithm. These figures are measurements from the current development environment, not guaranteed embedded-system performance.

#### 3.10 Task 2 Outputs

- `results/task02_benchmark.json`
- `results/task02_latency.csv`

The JSON file stores the benchmark summary. The CSV file records individual latency measurements for further analysis.

---

### Task 3 — Exception Handling and Structured Logging

**Objective:** Validate incoming sensor packets, handle invalid data safely, and record diagnostic events.

#### 3.11 Packet Validation

The monitoring utility checks that incoming packets:

- Are dictionaries.
- Contain a supported sensor identifier.
- Have a non-negative integer sequence number.
- Have a non-negative numeric timestamp.
- Contain a non-empty measurements dictionary.

Valid packets return `True`. Invalid packets trigger an appropriate validation exception, which is caught and logged; the function returns `False`.

#### 3.12 Structured Logging

The implementation writes JSON-formatted events to:

`logs/structured.log`

Log records can include:

- Timestamp
- Severity level
- Logger name
- Event message
- Task identifier
- Sensor identifier
- Sequence number
- Processing latency
- Exception details when applicable

Example successful event:

```json
{
  "level": "INFO",
  "logger": "embedded_ai",
  "message": "Packet validated",
  "task": "Task-03",
  "sensor": "IMU",
  "sequence": 1,
  "event": "packet_validated"
}
```

An invalid sensor type produces an error event with exception details.

Structured logs make failures easier to search, analyze, and diagnose than unstructured print statements.

#### 3.13 Error-Handling Scope

The current implementation handles expected packet validation errors. Unexpected system failures, hardware-driver errors, communication timeouts, and long-running recovery behavior require additional integration-specific handling.

---

## 4. System Architecture

```text
             Synthetic Sensor Data
                      |
          +-----------+-----------+
          |           |           |
         IMU       Acoustic      GPS
          |           |           |
          +-----------+-----------+
                      |
              Timestamp Alignment
                      |
              Missing Packet Recovery
                      |
                Task 1 Outputs
                      |
           +----------+-----------+
           |                      |
     Aligned Sensor Data     Acoustic Signals
                                  |
                            GCC-PHAT TDoA
                                  |
                         Performance Benchmark
                                  |
                         Task 2 Outputs

           All Tasks --> Validation and Logging
                                  |
                     CSV / JSON / Log Artifacts
```

---

## 5. Repository Structure

```text
RE-T1-FEVAL/
├── Task-01/
│   ├── sensor_ingestion.py
│   ├── timestamp_alignment.py
│   └── run_task01.py
│
├── Task-02/
│   ├── tdoa_estimator.py
│   └── benchmark_inference.py
│
├── Task-03/
│   └── monitoring.py
│
├── tests/
│   ├── test_task01.py
│   ├── test_task02.py
│   └── test_task03.py
│
├── results/
│   ├── sensor_alignment.csv
│   ├── task01_summary.json
│   ├── task02_benchmark.json
│   └── task02_latency.csv
│
├── logs/
│   ├── challenge.log
│   └── structured.log
│
├── .gitignore
└── README.md
```

Generated `__pycache__` directories may also appear when Python modules are executed. They are not required source files.

---

## 6. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core implementation |
| NumPy | Numeric arrays, FFT, interpolation, and signal processing |
| `unittest` | Automated testing |
| `time` | Execution latency measurement |
| `tracemalloc` | Python allocation tracking |
| `psutil` | Process memory information |
| `csv` | Tabular result export |
| `json` | Structured data and benchmark output |
| `logging` | Diagnostic events and exception reporting |
| Git and GitHub Codespaces | Version control and development environment |

---

## 7. Setup and Installation

### Prerequisites

- Python 3.14 or a compatible Python version
- Git
- A terminal or VS Code / GitHub Codespaces environment

### Install Dependencies

From the repository root:

```bash
python -m pip install numpy psutil
```

Confirm the environment:

```bash
python --version
python -m pip show numpy psutil
```

---

## 8. Running the Project

Run commands from the repository root.

### Task 1 — Generate and Align Sensor Streams

```bash
python Task-01/sensor_ingestion.py
python Task-01/run_task01.py
```

This generates synthetic sensor streams, simulates a three-packet loss, performs recovery and alignment, and writes the Task 1 outputs.

### Task 2 — Run TDoA Estimation

```bash
python Task-02/tdoa_estimator.py
```

This demonstrates the GCC-PHAT estimator on synthetic signals with a known delay.

### Task 2 — Run Performance Benchmark

```bash
python Task-02/benchmark_inference.py
```

This performs the 100-iteration benchmark and writes the latency CSV and benchmark JSON files.

### Task 3 — Run Logging Demonstration

```bash
python Task-03/monitoring.py
```

This validates a sample packet, deliberately processes an invalid packet, and demonstrates success and error logging.

### Run the Complete Automated Test Suite

```bash
python -m unittest discover -s tests -v
```

The test suite covers packet recovery, timestamp alignment, known acoustic delays, invalid signal inputs, and packet validation.

---

## 9. Automated Testing

The latest recorded test run completed with **11 tests passing**.

| Test module | Test coverage | Result |
|---|---|---|
| `test_task01.py` | Three-packet recovery and timestamp alignment | Passed |
| `test_task02.py` | Multiple known delays and invalid signal inputs | Passed |
| `test_task03.py` | Valid packets and rejected invalid packets | Passed |
| **Total** | **11 automated tests** | **11 passed** |

The test suite provides repeatable checks for the implemented behaviors. It does not replace hardware-in-the-loop testing or validation against real sensor data.

---

## 10. Output Artifacts

### Task 1

**`results/sensor_alignment.csv`**

Contains aligned timestamps, sensor names, JSON-encoded measurements, and estimation flags.

**`results/task01_summary.json`**

Contains stream counts, recovery count, and alignment row counts.

### Task 2

**`results/task02_benchmark.json`**

Contains expected and estimated delays, latency statistics, and memory metrics.

**`results/task02_latency.csv`**

Contains per-iteration latency measurements for analysis or plotting.

### Logs

**`logs/challenge.log`**

Contains integration logs for the Task 1 workflow.

**`logs/structured.log`**

Contains structured Task 3 packet validation and exception events.

---

## 11. Current Limitations and Future Improvements

### Current Limitations

1. Sensor data is synthetic; real sensor drivers and communication links are not integrated.
2. Timestamp alignment uses numeric interpolation and does not model all clock drift or synchronization problems.
3. Packet recovery has been tested with a three-packet synthetic gap, not with a live unreliable sensor link.
4. TDoA validation uses synthetic signals rather than recorded microphone data.
5. Acoustic source localization requires microphone geometry and additional spatial estimation logic, which are not implemented here.
6. Benchmark measurements come from the current development environment and are not hard real-time guarantees.
7. Structured logging covers the current validation workflow; production-grade monitoring and hardware error recovery need further development.

### Future Improvements

- Integrate physical IMU, microphone, and GPS interfaces.
- Test timestamp alignment with real asynchronous packet arrivals and clock drift.
- Evaluate TDoA under noise, reverberation, and varying signal-to-noise ratios.
- Extend testing to positive and negative delay conventions and different sampling rates.
- Add configurable profiling runs and percentile latency statistics.
- Measure peak process RSS and CPU utilization over sustained workloads.
- Add hardware-in-the-loop and long-duration stress tests.
- Add continuous integration to run unit tests on every push.

---

## 12. Conclusion

This project demonstrates a modular implementation of multi-sensor data processing, bounded missing-packet recovery, timestamp alignment, GCC-PHAT-based acoustic delay estimation, performance profiling, and structured error logging.

The current implementation has passed its 11-test synthetic-data test suite. The benchmark and output files provide a reproducible starting point for future integration with real acoustic and embedded sensing hardware.

**Project status:** Core implementation and synthetic validation complete; real-world and hardware validation remain future work.
