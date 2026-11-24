"""Estimate ideal compute, memory, and host-device transfer lower bounds."""

from __future__ import annotations

import argparse
import json
import math


def estimate(
    work_tflop: float,
    memory_gb: float,
    peak_tflops: float,
    memory_bandwidth_gb_s: float,
    transfer_gb: float,
    link_bandwidth_gb_s: float,
) -> dict:
    values = (
        work_tflop,
        memory_gb,
        peak_tflops,
        memory_bandwidth_gb_s,
        transfer_gb,
        link_bandwidth_gb_s,
    )
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError("all workload and hardware values must be positive and finite")
    work_flop = work_tflop * 1e12
    memory_bytes = memory_gb * 1e9
    arithmetic_intensity = work_flop / memory_bytes
    ridge_point = peak_tflops * 1e12 / (memory_bandwidth_gb_s * 1e9)
    compute_ms = work_tflop / peak_tflops * 1000
    memory_ms = memory_gb / memory_bandwidth_gb_s * 1000
    lower_bound_ms = max(compute_ms, memory_ms)
    attainable_tflops = min(
        peak_tflops,
        memory_bandwidth_gb_s * 1e9 * arithmetic_intensity / 1e12,
    )
    return {
        "assumptions": {
            "work_tflop": work_tflop,
            "memory_gb": memory_gb,
            "peak_tflops": peak_tflops,
            "memory_bandwidth_gb_s": memory_bandwidth_gb_s,
            "transfer_gb": transfer_gb,
            "link_bandwidth_gb_s": link_bandwidth_gb_s,
            "unit_note": "GB and GB/s are decimal units; 1 GB = 1e9 bytes.",
        },
        "arithmetic_intensity_flop_per_byte": arithmetic_intensity,
        "ridge_point_flop_per_byte": ridge_point,
        "ideal_compute_time_ms": compute_ms,
        "ideal_memory_time_ms": memory_ms,
        "roofline_lower_bound_ms": lower_bound_ms,
        "roofline_ceiling_tflops": attainable_tflops,
        "roofline_region": "memory-bound" if arithmetic_intensity < ridge_point else "compute-bound",
        "ideal_host_device_transfer_ms": transfer_gb / link_bandwidth_gb_s * 1000,
        "limits": [
            "All results are ideal lower bounds, not measured runtime.",
            "The model assumes compute and memory time overlap perfectly at the slower bound.",
            "It excludes launch, synchronization, latency, cache, layout, and contention effects.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-tflop", type=float, default=1)
    parser.add_argument("--memory-gb", type=float, default=100)
    parser.add_argument("--peak-tflops", type=float, default=100)
    parser.add_argument("--memory-bandwidth-gb-s", type=float, default=2000)
    parser.add_argument("--transfer-gb", type=float, default=14)
    parser.add_argument("--link-bandwidth-gb-s", type=float, default=64)
    args = parser.parse_args()
    try:
        report = estimate(**vars(args))
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
