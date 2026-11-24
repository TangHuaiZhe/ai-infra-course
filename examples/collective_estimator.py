"""Estimate ideal per-device traffic for ring collective communication."""

from __future__ import annotations

import argparse
import json
import math


GIB = 1024**3
COLLECTIVES = ("all-reduce", "all-gather", "reduce-scatter")


def estimate(collective: str, devices: int, payload_gib: float, bandwidth_gb_s: float) -> dict:
    if collective not in COLLECTIVES:
        raise ValueError(f"collective must be one of: {', '.join(COLLECTIVES)}")
    if devices < 2:
        raise ValueError("devices must be at least 2")
    if any(not math.isfinite(value) or value <= 0 for value in (payload_gib, bandwidth_gb_s)):
        raise ValueError("payload and bandwidth must be positive and finite")
    phase_factor = 2 if collective == "all-reduce" else 1
    traffic_factor = phase_factor * (devices - 1) / devices
    traffic_gib = payload_gib * traffic_factor
    traffic_bytes = traffic_gib * GIB
    ideal_time_ms = traffic_bytes / (bandwidth_gb_s * 1e9) * 1000
    return {
        "collective": collective,
        "devices": devices,
        "logical_payload_gib": payload_gib,
        "assumed_effective_bandwidth_gb_s": bandwidth_gb_s,
        "ideal_traffic_factor_per_device": traffic_factor,
        "ideal_traffic_gib_per_device": traffic_gib,
        "ideal_bandwidth_time_ms": ideal_time_ms,
        "limits": [
            "This is a balanced ring traffic model, not an NCCL execution prediction.",
            "Bandwidth is a user-supplied effective per-device value in decimal GB/s.",
            "The estimate excludes latency, protocol overhead, topology imbalance, and contention.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collective", choices=COLLECTIVES, action="append")
    parser.add_argument("--devices", type=int, default=8)
    parser.add_argument("--payload-gib", type=float, default=4)
    parser.add_argument("--bandwidth-gb-s", type=float, default=400)
    args = parser.parse_args()
    collectives = args.collective or list(COLLECTIVES)
    try:
        reports = [
            estimate(name, args.devices, args.payload_gib, args.bandwidth_gb_s)
            for name in collectives
        ]
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
