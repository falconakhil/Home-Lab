
#!/usr/bin/env python3
import argparse
import math
import os
import random
import shutil
import statistics
import subprocess
import tempfile
import time
import hashlib
from pathlib import Path


def run_fio(path: Path, size_mib: int) -> float:
    """Run random 4 KiB writes and return elapsed wall-clock seconds."""
    command = [
        "fio",
        "--name=staging-bench",
        f"--filename={path}",
        f"--size={size_mib}M",
        "--rw=randwrite",
        "--bs=4k",
        "--ioengine=psync",
        "--iodepth=1",
        "--direct=1",
        "--end_fsync=1",
        "--randseed=12345",
        "--group_reporting",
    ]

    start = time.monotonic()
    subprocess.run(command, check=True)
    return time.monotonic() - start


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def timed_sync() -> None:
    """Request filesystem writeback."""
    subprocess.run(["sync"], check=True)


def run_direct(hdd: Path, size_mib: int, trial: int) -> float:
    destination = hdd / f".bench-direct-{os.getpid()}-{trial}"
    destination.unlink(missing_ok=True)

    print(f"\nTrial {trial}: random writes directly to HDD")
    try:
        elapsed = run_fio(destination, size_mib)
        timed_sync()
        print(f"Direct elapsed: {elapsed:.3f} seconds")
        return elapsed
    finally:
        destination.unlink(missing_ok=True)


def run_staged(
    ssd: Path, hdd: Path, size_mib: int, trial: int
) -> float:
    source = ssd / f".bench-stage-{os.getpid()}-{trial}"
    destination = hdd / f".bench-stage-{os.getpid()}-{trial}"

    source.unlink(missing_ok=True)
    destination.unlink(missing_ok=True)

    print(f"\nTrial {trial}: random writes to SSD, then copy to HDD")
    start = time.monotonic()

    try:
        run_fio(source, size_mib)

        # Copy the completed file to the HDD sequentially.
        shutil.copyfile(source, destination)
        timed_sync()

        elapsed = time.monotonic() - start

        print("Verifying copied data...")
        if sha256(source) != sha256(destination):
            raise RuntimeError("Data integrity verification failed!")

        print(f"Staged end-to-end elapsed: {elapsed:.3f} seconds")
        print("Data integrity: PASS")
        return elapsed
    finally:
        source.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Compare direct HDD random writes with SSD staging."
    )
    parser.add_argument("ssd", type=Path, help="Directory on SSD")
    parser.add_argument("hdd", type=Path, help="Directory on HDD")
    parser.add_argument("--size-mib", type=int, default=128)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    ssd = args.ssd.resolve()
    hdd = args.hdd.resolve()

    if not ssd.is_dir() or not hdd.is_dir():
        parser.error("Both directories must already exist.")
    if args.size_mib < 1 or args.repeats < 1:
        parser.error("Size and repetitions must be positive.")
    if shutil.disk_usage(ssd).free < args.size_mib * 1024**2 + 16*1024**2:
        parser.error("Insufficient free space on SSD.")
    if shutil.disk_usage(hdd).free < args.size_mib * 1024**2 + 16*1024**2:
        parser.error("Insufficient free space on HDD.")

    if os.stat(ssd).st_dev == os.stat(hdd).st_dev:
        parser.error("SSD and HDD paths appear to be on the same filesystem.")

    print(f"SSD: {ssd}")
    print(f"HDD: {hdd}")
    print(f"Random-write test size: {args.size_mib} MiB")
    print(f"Trials per method: {args.repeats}")
    print("\nWARNING: These tests write temporary files to both devices.")

    direct_times = []
    staged_times = []

    # Alternate order to reduce ordering bias.
    for trial in range(1, args.repeats + 1):
        if trial % 2:
            direct_times.append(run_direct(hdd, args.size_mib, trial))
            staged_times.append(run_staged(ssd, hdd, args.size_mib, trial))
        else:
            staged_times.append(run_staged(ssd, hdd, args.size_mib, trial))
            direct_times.append(run_direct(hdd, args.size_mib, trial))

    direct = statistics.median(direct_times)
    staged = statistics.median(staged_times)

    print("\n========== RESULTS ==========")
    print(f"Direct HDD median: {direct:.3f} seconds")
    print(f"SSD staging median: {staged:.3f} seconds")

    print(f"Time reduction: {(direct-staged)/direct*100:.2f}%")
    print(f"Effective throughput gain: {(direct/staged-1)*100:.2f}%")

    print("\nIndividual trials:")
    for i, (d, s) in enumerate(zip(direct_times, staged_times), 1):
        print(f"Trial {i}: direct={d:.3f}s, staged={s:.3f}s")


if __name__ == "__main__":
    main()

