"""Simulate quota, gang allocation, topology, priority, and node outages."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def parse_bool(value: str, line: int) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"line {line}: same_node must be true or false")


def load_jobs(path: Path) -> list[dict]:
    required = {"job_id", "arrival_ms", "tenant", "gpus", "duration_ms", "priority", "same_node"}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV requires columns: {', '.join(sorted(required))}")
        jobs = []
        seen = set()
        previous_arrival = -1.0
        for index, raw in enumerate(reader):
            line = index + 2
            try:
                job_id = raw["job_id"].strip()
                tenant = raw["tenant"].strip()
                arrival_ms = float(raw["arrival_ms"])
                gpus = int(raw["gpus"])
                duration_ms = float(raw["duration_ms"])
                priority = int(raw["priority"])
                same_node = parse_bool(raw["same_node"], line)
            except (TypeError, ValueError) as error:
                if isinstance(error, ValueError) and str(error).startswith("line "):
                    raise
                raise ValueError(f"line {line}: invalid numeric or boolean value") from error
            numeric = (arrival_ms, duration_ms, float(gpus), float(priority))
            if not job_id or job_id in seen or not tenant:
                raise ValueError(f"line {line}: job_id must be unique and tenant must be nonempty")
            if any(not math.isfinite(value) for value in numeric):
                raise ValueError(f"line {line}: numeric values must be finite")
            if arrival_ms < previous_arrival or arrival_ms < 0 or gpus < 1 or duration_ms <= 0:
                raise ValueError(f"line {line}: arrivals must be ordered; resources and duration must be positive")
            seen.add(job_id)
            previous_arrival = arrival_ms
            jobs.append({
                "index": index,
                "job_id": job_id,
                "arrival_ms": arrival_ms,
                "tenant": tenant,
                "gpus": gpus,
                "duration_ms": duration_ms,
                "priority": priority,
                "same_node": same_node,
            })
    if not jobs:
        raise ValueError("workload has no jobs")
    return jobs


def parse_quota(value: str) -> tuple[str, int]:
    try:
        tenant, raw_limit = value.split("=", 1)
        limit = int(raw_limit)
    except ValueError as error:
        raise argparse.ArgumentTypeError("use TENANT=GPUS") from error
    if not tenant or limit < 1:
        raise argparse.ArgumentTypeError("quota requires a tenant and a positive GPU count")
    return tenant, limit


def parse_outage(value: str) -> tuple[str, float, float]:
    try:
        node, raw_start, raw_end = value.split(":")
        start, end = float(raw_start), float(raw_end)
    except ValueError as error:
        raise argparse.ArgumentTypeError("use NODE:START_MS:END_MS") from error
    if not node or not 0 <= start < end:
        raise argparse.ArgumentTypeError("outage requires a node and 0 <= start < end")
    return node, start, end


def nearest_rank(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * fraction) - 1]


def node_ready(node: str, time_ms: float, outages: list[tuple[str, float, float]]) -> bool:
    return not any(name == node and start <= time_ms < end for name, start, end in outages)


def allocate(
    job: dict,
    time_ms: float,
    nodes: list[str],
    gpus_per_node: int,
    running: list[dict],
    outages: list[tuple[str, float, float]],
) -> dict[str, int] | None:
    used = {node: 0 for node in nodes}
    for active in running:
        for node, count in active["allocation"].items():
            used[node] += count
    free = {
        node: gpus_per_node - used[node] if node_ready(node, time_ms, outages) else 0
        for node in nodes
    }
    if job["same_node"]:
        candidates = [node for node in nodes if free[node] >= job["gpus"]]
        if not candidates:
            return None
        chosen = min(candidates, key=lambda node: (free[node] - job["gpus"], node))
        return {chosen: job["gpus"]}
    remaining = job["gpus"]
    allocation = {}
    for node in sorted(nodes, key=lambda name: (-free[name], name)):
        count = min(remaining, free[node])
        if count:
            allocation[node] = count
            remaining -= count
        if remaining == 0:
            return allocation
    return None


def simulate(
    jobs: list[dict],
    policy: str,
    node_count: int,
    gpus_per_node: int,
    quotas: dict[str, int],
    outages: list[tuple[str, float, float]],
) -> dict:
    if policy not in {"fifo", "priority"}:
        raise ValueError("policy must be fifo or priority")
    if node_count < 1 or gpus_per_node < 1:
        raise ValueError("node_count and gpus_per_node must be positive")
    nodes = [f"node-{index}" for index in range(node_count)]
    unknown_nodes = sorted({item[0] for item in outages} - set(nodes))
    if unknown_nodes:
        raise ValueError(f"outage names unknown node: {', '.join(unknown_nodes)}")
    total_gpus = node_count * gpus_per_node
    results = {}
    pending = []
    future = list(jobs)
    running = []
    boundaries = sorted({time for _, start, end in outages for time in (start, end)})
    time_ms = jobs[0]["arrival_ms"]

    for job in jobs:
        quota = quotas.get(job["tenant"], total_gpus)
        impossible = job["gpus"] > total_gpus or job["gpus"] > quota
        impossible = impossible or (job["same_node"] and job["gpus"] > gpus_per_node)
        if impossible:
            results[job["job_id"]] = {"job_id": job["job_id"], "status": "unschedulable"}

    future = [job for job in future if job["job_id"] not in results]
    while future or pending or running:
        completed = [active for active in running if active["end_ms"] <= time_ms]
        running = [active for active in running if active["end_ms"] > time_ms]
        for active in completed:
            result = results[active["job_id"]]
            result["status"] = "completed"

        arrived = [job for job in future if job["arrival_ms"] <= time_ms]
        future = [job for job in future if job["arrival_ms"] > time_ms]
        pending.extend(arrived)

        started_any = True
        while started_any:
            started_any = False
            tenant_used = {}
            for active in running:
                tenant_used[active["tenant"]] = tenant_used.get(active["tenant"], 0) + active["gpus"]
            if policy == "fifo":
                ordered = sorted(pending, key=lambda job: (job["arrival_ms"], job["index"]))
            else:
                ordered = sorted(pending, key=lambda job: (-job["priority"], job["arrival_ms"], job["index"]))
            for job in ordered:
                quota = quotas.get(job["tenant"], total_gpus)
                if tenant_used.get(job["tenant"], 0) + job["gpus"] > quota:
                    continue
                allocation = allocate(job, time_ms, nodes, gpus_per_node, running, outages)
                if allocation is None:
                    continue
                end_ms = time_ms + job["duration_ms"]
                active = {**job, "start_ms": time_ms, "end_ms": end_ms, "allocation": allocation}
                running.append(active)
                pending.remove(job)
                results[job["job_id"]] = {
                    "job_id": job["job_id"],
                    "status": "running",
                    "start_ms": time_ms,
                    "end_ms": end_ms,
                    "wait_ms": time_ms - job["arrival_ms"],
                    "allocation": allocation,
                }
                started_any = True
                break

        if not (future or pending or running):
            break
        next_times = [job["arrival_ms"] for job in future]
        next_times.extend(active["end_ms"] for active in running)
        next_times.extend(boundary for boundary in boundaries if boundary > time_ms)
        if not next_times:
            for job in pending:
                results[job["job_id"]] = {"job_id": job["job_id"], "status": "unschedulable"}
            pending.clear()
            break
        next_time = min(next_times)
        if next_time <= time_ms:
            raise RuntimeError("simulation did not advance")
        time_ms = next_time

    ordered_results = [results[job["job_id"]] for job in jobs]
    completed = [result for result in ordered_results if result["status"] == "completed"]
    waits = [result["wait_ms"] for result in completed]
    return {
        "policy": policy,
        "cluster": {"nodes": node_count, "gpus_per_node": gpus_per_node, "total_gpus": total_gpus},
        "quotas": quotas,
        "outages": [{"node": node, "start_ms": start, "end_ms": end} for node, start, end in outages],
        "jobs": len(jobs),
        "completed": len(completed),
        "unschedulable": sum(result["status"] == "unschedulable" for result in ordered_results),
        "mean_wait_ms": sum(waits) / len(waits) if waits else None,
        "p95_wait_ms": nearest_rank(waits, 0.95),
        "schedule": ordered_results,
        "limits": [
            "Jobs are allocated as an all-or-nothing group and are never preempted.",
            "A node outage blocks new placements only; running jobs are not interrupted.",
            "The simulator omits containers, startup time, retries, autoscaling, and real topology costs.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--policy", choices=("fifo", "priority"), action="append")
    parser.add_argument("--nodes", type=int, default=2)
    parser.add_argument("--gpus-per-node", type=int, default=4)
    parser.add_argument("--quota", type=parse_quota, action="append", default=[])
    parser.add_argument("--outage", type=parse_outage, action="append", default=[])
    args = parser.parse_args()
    policies = args.policy or ["fifo", "priority"]
    quotas = dict(args.quota)
    try:
        jobs = load_jobs(args.csv_file)
        reports = [
            simulate(jobs, policy, args.nodes, args.gpus_per_node, quotas, args.outage)
            for policy in policies
        ]
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
