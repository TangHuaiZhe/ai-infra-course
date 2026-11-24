"""Summarize a streamed inference request trace without third-party packages."""

import argparse
import csv
import json
import math
from pathlib import Path


def percentile(values: list[float], fraction: float) -> float:
    """Return the nearest-rank percentile of a nonempty sample."""
    if not values or not 0 < fraction <= 1:
        raise ValueError("percentile requires data and a fraction in (0, 1]")
    ordered = sorted(values)
    return ordered[math.ceil(fraction * len(ordered)) - 1]


def load_trace(path: Path) -> list[dict]:
    required = {"request_id", "arrival_ms", "first_token_ms", "end_ms", "output_tokens"}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV requires columns: {', '.join(sorted(required))}")
        rows = []
        seen = set()
        for line, raw in enumerate(reader, start=2):
            try:
                request_id = raw["request_id"].strip()
                arrival = float(raw["arrival_ms"])
                first = float(raw["first_token_ms"])
                end = float(raw["end_ms"])
                tokens = int(raw["output_tokens"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"line {line}: invalid numeric value") from error
            if not request_id or request_id in seen:
                raise ValueError(f"line {line}: empty or duplicate request_id")
            if not all(math.isfinite(v) for v in (arrival, first, end)):
                raise ValueError(f"line {line}: time values must be finite")
            if not 0 <= arrival <= first <= end or tokens < 1:
                raise ValueError(f"line {line}: require 0 <= arrival <= first <= end and output_tokens >= 1")
            seen.add(request_id)
            rows.append({"request_id": request_id, "arrival": arrival, "first": first, "end": end, "tokens": tokens})
    if not rows:
        raise ValueError("trace has no requests")
    return rows


def summarize(rows: list[dict], ttft_limit_ms: float, tpot_limit_ms: float, e2e_limit_ms: float) -> dict:
    if min(ttft_limit_ms, tpot_limit_ms, e2e_limit_ms) <= 0:
        raise ValueError("SLO limits must be positive")
    span_ms = max(row["end"] for row in rows) - min(row["arrival"] for row in rows)
    if span_ms <= 0:
        raise ValueError("trace duration must be positive")
    ttfts = [row["first"] - row["arrival"] for row in rows]
    e2es = [row["end"] - row["arrival"] for row in rows]
    tpots = [(row["end"] - row["first"]) / (row["tokens"] - 1) for row in rows if row["tokens"] > 1]
    good = sum(
        ttft <= ttft_limit_ms
        and e2e <= e2e_limit_ms
        and (row["tokens"] == 1 or (row["end"] - row["first"]) / (row["tokens"] - 1) <= tpot_limit_ms)
        for row, ttft, e2e in zip(rows, ttfts, e2es)
    )
    seconds = span_ms / 1000
    return {
        "requests": len(rows),
        "duration_s": seconds,
        "ttft_ms_p50": percentile(ttfts, 0.5),
        "ttft_ms_p95": percentile(ttfts, 0.95),
        "e2e_ms_p95": percentile(e2es, 0.95),
        "tpot_ms_p50": percentile(tpots, 0.5) if tpots else None,
        "tpot_defined_requests": len(tpots),
        "output_tokens_per_s": sum(row["tokens"] for row in rows) / seconds,
        "good_requests": good,
        "good_requests_per_s": good / seconds,
        "slo": {"ttft_ms": ttft_limit_ms, "tpot_ms": tpot_limit_ms, "e2e_ms": e2e_limit_ms},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--slo-ttft-ms", type=float, default=500)
    parser.add_argument("--slo-tpot-ms", type=float, default=200)
    parser.add_argument("--slo-e2e-ms", type=float, default=2000)
    args = parser.parse_args()
    try:
        report = summarize(load_trace(args.csv_file), args.slo_ttft_ms, args.slo_tpot_ms, args.slo_e2e_ms)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
