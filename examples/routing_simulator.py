"""Compare replica routing policies with a deterministic teaching simulation."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Replica:
    name: str
    available_ms: float = 0
    cached_prefixes: set[str] = field(default_factory=set)


def percentile(values: list[float], fraction: float) -> float | None:
    """Return the nearest-rank percentile, or None for an empty sample."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * fraction) - 1]


def load_requests(path: Path) -> list[dict]:
    required = {"request_id", "arrival_ms", "prefix", "service_ms"}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV requires columns: {', '.join(sorted(required))}")
        rows = []
        seen = set()
        previous_arrival = -1.0
        for line, raw in enumerate(reader, start=2):
            try:
                request_id = raw["request_id"].strip()
                arrival_ms = float(raw["arrival_ms"])
                prefix = raw["prefix"].strip()
                service_ms = float(raw["service_ms"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"line {line}: invalid value") from error
            if not request_id or request_id in seen or not prefix:
                raise ValueError(f"line {line}: request_id must be unique and prefix must be nonempty")
            if not all(math.isfinite(value) for value in (arrival_ms, service_ms)):
                raise ValueError(f"line {line}: numeric values must be finite")
            if arrival_ms < previous_arrival or arrival_ms < 0 or service_ms <= 0:
                raise ValueError(f"line {line}: arrivals must be ordered and nonnegative; service_ms must be positive")
            seen.add(request_id)
            previous_arrival = arrival_ms
            rows.append({
                "request_id": request_id,
                "arrival_ms": arrival_ms,
                "prefix": prefix,
                "service_ms": service_ms,
            })
    if not rows:
        raise ValueError("trace has no requests")
    return rows


def parse_failure(value: str) -> tuple[str, float, float]:
    try:
        replica, start, end = value.split(":")
        start_ms, end_ms = float(start), float(end)
    except ValueError as error:
        raise argparse.ArgumentTypeError("use REPLICA:START_MS:END_MS") from error
    if not replica or not 0 <= start_ms < end_ms:
        raise argparse.ArgumentTypeError("failure requires a replica and 0 <= start < end")
    return replica, start_ms, end_ms


def is_ready(name: str, arrival_ms: float, failures: list[tuple[str, float, float]]) -> bool:
    return not any(replica == name and start <= arrival_ms < end for replica, start, end in failures)


def simulate(
    requests: list[dict],
    policy: str,
    replica_count: int,
    cache_saving_ms: float,
    max_affinity_wait_ms: float,
    failures: list[tuple[str, float, float]],
) -> dict:
    if replica_count < 1 or cache_saving_ms < 0 or max_affinity_wait_ms < 0:
        raise ValueError("replicas must be positive; timing options must be nonnegative")
    replicas = [Replica(f"replica-{index}") for index in range(replica_count)]
    names = {replica.name for replica in replicas}
    unknown = sorted({failure[0] for failure in failures} - names)
    if unknown:
        raise ValueError(f"failure names unknown replica: {', '.join(unknown)}")
    results = []
    for request in requests:
        arrival = request["arrival_ms"]
        ready = [replica for replica in replicas if is_ready(replica.name, arrival, failures)]
        if not ready:
            results.append({"request_id": request["request_id"], "status": "rejected"})
            continue
        queue_by_name = {replica.name: max(0.0, replica.available_ms - arrival) for replica in ready}
        least_queue = min(queue_by_name.values())
        candidates = ready
        if policy == "prefix-affinity":
            affinity = [
                replica for replica in ready
                if request["prefix"] in replica.cached_prefixes
                and queue_by_name[replica.name] <= least_queue + max_affinity_wait_ms
            ]
            if affinity:
                candidates = affinity
        chosen = min(candidates, key=lambda replica: (queue_by_name[replica.name], replica.name))
        cache_hit = request["prefix"] in chosen.cached_prefixes
        start = max(arrival, chosen.available_ms)
        duration = max(1.0, request["service_ms"] - (cache_saving_ms if cache_hit else 0.0))
        end = start + duration
        chosen.available_ms = end
        chosen.cached_prefixes.add(request["prefix"])
        results.append({
            "request_id": request["request_id"],
            "replica": chosen.name,
            "cache_hit": cache_hit,
            "queue_ms": start - arrival,
            "end_to_end_ms": end - arrival,
            "status": "completed",
        })
    completed = [result for result in results if result["status"] == "completed"]
    hits = sum(result["cache_hit"] for result in completed)
    return {
        "policy": policy,
        "requests": len(requests),
        "completed": len(completed),
        "rejected": len(requests) - len(completed),
        "cache_hits": hits,
        "cache_hit_rate": hits / len(completed) if completed else None,
        "mean_queue_ms": sum(result["queue_ms"] for result in completed) / len(completed) if completed else None,
        "p95_end_to_end_ms": percentile([result["end_to_end_ms"] for result in completed], 0.95),
        "assignments": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--policy", choices=("least-queue", "prefix-affinity"), action="append")
    parser.add_argument("--replicas", type=int, default=2)
    parser.add_argument("--cache-saving-ms", type=float, default=80)
    parser.add_argument("--max-affinity-wait-ms", type=float, default=100)
    parser.add_argument("--failure", type=parse_failure, action="append", default=[])
    args = parser.parse_args()
    policies = args.policy or ["least-queue", "prefix-affinity"]
    try:
        requests = load_requests(args.csv_file)
        reports = [
            simulate(
                requests,
                policy,
                args.replicas,
                args.cache_saving_ms,
                args.max_affinity_wait_ms,
                args.failure,
            )
            for policy in policies
        ]
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
