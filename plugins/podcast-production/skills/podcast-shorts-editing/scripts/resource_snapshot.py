#!/usr/bin/env python3
"""Read-only, bounded macOS resource sampling; writes an observational JSON report.

No Adobe commands, preference changes, cache cleanup, process termination, or
background service. RSS is resident-set size, not macOS physical footprint.
"""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


GIB = 1024 ** 3
RELEVANT = re.compile(
    r"adobe|after effects|premiere|aerender|dynamiclink|ffmpeg|ffprobe|"
    r"whisper|diariz|mlx|torch|python", re.I
)


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def command(argv):
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    if proc.returncode:
        return None, proc.stderr.strip() or f"exit {proc.returncode}"
    return proc.stdout.strip(), None


def sysctl_value(key):
    raw, error = command(["/usr/sbin/sysctl", "-n", key])
    return {"raw": raw, "error": error}


def int_or_none(raw):
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


def disk_snapshot(path):
    result = {"path": str(path), "total_bytes": None, "used_bytes": None,
              "free_bytes": None, "error": None}
    try:
        usage = shutil.disk_usage(path)
        result.update(total_bytes=usage.total, used_bytes=usage.used,
                      free_bytes=usage.free)
    except OSError as exc:
        result["error"] = str(exc)
    return result


def process_snapshot():
    # comm contains the executable name/path, never the process's arguments.
    raw, error = command(["/bin/ps", "-axo", "pid=,rss=,comm="])
    if raw is None:
        return {"top_10_rss": None, "relevant_processes": None, "error": error}
    rows = []
    for line in raw.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) != 3:
            continue
        pid, rss_kib = int_or_none(fields[0]), int_or_none(fields[1])
        if pid is None or rss_kib is None:
            continue
        rows.append({"pid": pid, "name": os.path.basename(fields[2]),
                     "rss_bytes": rss_kib * 1024})
    rows.sort(key=lambda item: item["rss_bytes"], reverse=True)
    return {"top_10_rss": rows[:10],
            "relevant_processes": [row for row in rows if RELEVANT.search(row["name"])],
            "error": error}


def vm_snapshot():
    raw, error = command(["/usr/bin/vm_stat"])
    result = {"page_size_bytes": None, "counters": None,
              "compressor_bytes": None, "pages_stored_in_compressor_bytes": None,
              "swapins_pages_since_boot": None, "swapouts_pages_since_boot": None,
              "error": error}
    if raw is None:
        return result
    match = re.search(r"page size of (\d+) bytes", raw)
    page_size = int(match.group(1)) if match else None
    counters = {}
    for line in raw.splitlines()[1:]:
        match = re.match(r"([^:]+):\s*(\d+)\.?\s*$", line)
        if match:
            counters[match.group(1).strip()] = int(match.group(2))
    result.update(page_size_bytes=page_size, counters=counters)
    if page_size is not None:
        for source, dest in (("Pages occupied by compressor", "compressor_bytes"),
                             ("Pages stored in compressor", "pages_stored_in_compressor_bytes")):
            if source in counters:
                result[dest] = counters[source] * page_size
    result["swapins_pages_since_boot"] = counters.get("Swapins")
    result["swapouts_pages_since_boot"] = counters.get("Swapouts")
    return result


def snapshot(project_path):
    keys = ("hw.memsize", "kern.boottime", "kern.memorystatus_vm_pressure_level", "vm.swapusage")
    values = {key: sysctl_value(key) for key in keys}
    boot_raw = values["kern.boottime"]["raw"]
    boot_match = re.search(r"sec\s*=\s*(\d+)", boot_raw or "")
    boot_sec = int(boot_match.group(1)) if boot_match else None
    swap_raw = values["vm.swapusage"]["raw"]
    swap = {"total_bytes": None, "used_bytes": None, "free_bytes": None}
    for match in re.finditer(r"(total|used|free)\s*=\s*([\d.]+)([KMGT]?)", swap_raw or ""):
        power = {"": 0, "K": 1, "M": 2, "G": 3, "T": 4}[match.group(3)]
        swap[match.group(1) + "_bytes"] = round(float(match.group(2)) * 1024 ** power)
    disks = {"startup": disk_snapshot("/")}
    if project_path:
        disks["project"] = disk_snapshot(project_path)
    return {
        "timestamp_utc": utc_now(),
        "physical_memory_bytes": int_or_none(values["hw.memsize"]["raw"]),
        "boot_epoch_seconds": boot_sec,
        "uptime_seconds": round(time.time() - boot_sec, 3) if boot_sec else None,
        "memory_pressure_raw_flag": int_or_none(values["kern.memorystatus_vm_pressure_level"]["raw"]),
        "sysctl": values, "swap": swap, "vm_stat": vm_snapshot(),
        "disks": disks, "processes": process_snapshot(),
    }


def gib(value):
    return "unknown" if value is None else f"{value / GIB:.2f} GiB"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", type=Path, help="Optional existing media/project volume path to measure")
    parser.add_argument("--output", type=Path, help="JSON report path; defaults beside this script with UTC timestamp")
    parser.add_argument("--samples", type=int, default=1, help="1–60 samples; default 1")
    parser.add_argument("--interval", type=float, default=15, help="Seconds between samples, 1–60; default 15")
    args = parser.parse_args()
    if not 1 <= args.samples <= 60:
        parser.error("--samples must be between 1 and 60")
    if not 1 <= args.interval <= 60:
        parser.error("--interval must be between 1 and 60 seconds")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.output or Path(__file__).parent / f"resource-snapshot-{stamp}.json"
    if output.exists():
        parser.error(f"report already exists: {output}")
    if not output.parent.is_dir():
        parser.error(f"report directory does not exist: {output.parent}")
    report = {
        "schema_version": 1, "created_utc": utc_now(),
        "notes": [
            "Observational samples only; no pass guarantee, diagnosis, or automatic action.",
            "Process RSS is resident-set size, not macOS physical footprint; shared pages can be counted more than once.",
            "Process output includes executable basenames only, never full command arguments.",
            "Python process matches are possible ASR helpers, not proof that transcription is running.",
            "memory_pressure_raw_flag is the kernel's raw flag, not a percent-free estimate or reconstructed Activity Monitor graph.",
            "Missing or unavailable measurements are null, not zero.",
            "VM swap-in/out counters accumulate since boot; compare successive samples for current activity.",
            "Disk free bytes reflect filesystem availability, not a guarantee of safe export/cache capacity.",
        ],
        "requested_samples": args.samples, "interval_seconds": args.interval,
        "samples": [],
    }
    # A bounded foreground loop, not a daemon or scheduler. Flush each sample so
    # an interrupted observation still leaves the measurements already taken.
    with output.open("x", encoding="utf-8") as handle:
        for index in range(args.samples):
            if index:
                time.sleep(args.interval)
            current = snapshot(args.project_path)
            report["samples"].append(current)
            handle.seek(0)
            json.dump(report, handle, indent=2)
            handle.write("\n")
            handle.truncate()
            handle.flush()
            pressure = current["memory_pressure_raw_flag"]
            pressure = "unknown" if pressure is None else str(pressure)
            print(f"Sample {index + 1}/{args.samples} {current['timestamp_utc']} | "
                  f"pressure flag {pressure} | swap {gib(current['swap']['used_bytes'])} | "
                  f"compressor {gib(current['vm_stat']['compressor_bytes'])} | "
                  f"startup free {gib(current['disks']['startup']['free_bytes'])}", flush=True)
    print(f"JSON: {output.resolve()}")


if __name__ == "__main__":
    main()
