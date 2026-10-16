# SSD-Staged Writes vs. SMR HDD

A benchmark evaluating whether staging random writes on an SSD before transferring the completed file sequentially to an SMR HDD can reduce write completion time.

## Overview

Shingled Magnetic Recording (SMR) HDDs can experience significant performance degradation under sustained random-write workloads. This experiment compares direct random writes to an HDD against an SSD-staged approach.

### Approaches

**Direct HDD writes**

```text
fio (4 KiB random writes) → SMR HDD
```

**SSD-staged writes**

```text
fio (4 KiB random writes) → SSD → Sequential file copy → SMR HDD
```

The benchmark measures end-to-end completion time, including the SSD write and subsequent HDD copy for the staged approach.

## Benchmark Results

**Workload:** 512 MiB of 4 KiB random writes  
**Trials:** 3 per approach  
**Summary:** Median completion time

| Metric | Direct HDD | SSD-Staged |
|---|---:|---:|
| Median completion time | 651.043 s | 27.938 s |
| Effective throughput | 0.79 MiB/s | 18.33 MiB/s |
| Data integrity verification | N/A | Passed |

### Performance Improvement

- **95.71% lower completion time**
- **23.3× effective throughput**
- **2,230.31% increase in effective throughput**

### Individual Trials

| Trial | Direct HDD (s) | SSD-Staged (s) |
|---|---:|---:|
| 1 | 616.287 | 17.837 |
| 2 | 651.043 | 27.938 |
| 3 | 655.546 | 37.806 |

The staged approach was faster in all three trials. However, the variation in staged completion time indicates that further testing would be useful to assess repeatability.

## Methodology

The benchmark uses `fio` to generate a random-write workload, with the following configuration:

| Parameter | Value |
|---|---|
| Block size | 4 KiB |
| I/O pattern | Random writes |
| I/O engine | `psync` |
| Queue depth | 1 |
| Direct I/O | Enabled |
| Final synchronization | Enabled |
| Test size | 512 MiB |
| Repetitions | 3 |

For the direct approach, `fio` writes the test file directly to the HDD.

For the staged approach, `fio` writes the test file to the SSD. The completed file is then copied to the HDD, followed by a filesystem synchronization request. The staged copy is verified using SHA-256.

The reported times are measured wall-clock completion times from the benchmark script.

## Running the Benchmark

### Prerequisites

- Python 3
- `fio`
- Separate SSD and HDD filesystems
- Sufficient free space on both filesystems

Install the required packages:

```sh
pkg install python3 fio
```

### Execute

```sh
python3 benchmark.py /path/to/ssd /path/to/hdd \
    --size-mib 512 \
    --repeats 3
```

Replace the paths with directories located on the actual SSD and HDD filesystems.

The script creates temporary benchmark files, reports individual trial results, computes median completion times, and verifies staged copies.

**Warning:** The benchmark writes data to both storage devices. Use dedicated test directories and avoid running it while other disk-intensive workloads are active.

## Interpretation

The results demonstrate a substantial performance difference between the two approaches under this particular synthetic workload.

The likely benefit is that the SSD absorbs the random-write workload while the HDD receives the completed file as a sequential copy. However, the experiment does not independently establish that SMR cache exhaustion is the sole cause of the slowdown.

The results also depend on drive state, caching, filesystem behavior, USB connectivity, and background activity.

## Limitations

- The workload is synthetic and does not reproduce every aspect of torrent downloads.
- The benchmark uses a relatively small number of trials.
- HDD cache state and prior drive activity can affect results.
- A filesystem synchronization request does not independently prove persistence across a power loss.
- The reported performance improvement applies to this benchmark configuration and should not be generalized to all workloads.

## Conclusion

For the tested 512 MiB random-write workload, SSD staging reduced median completion time from approximately 10.85 minutes to 27.94 seconds.
