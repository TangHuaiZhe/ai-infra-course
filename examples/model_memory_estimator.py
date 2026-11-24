"""Estimate selected Transformer memory quantities from explicit assumptions."""

from __future__ import annotations

import argparse
import json
import math


GIB = 1024**3


def estimate(
    parameters_billions: float,
    weight_bytes: float,
    layers: int,
    attention_heads: int,
    kv_heads: int,
    head_dim: int,
    sequences: int,
    tokens_per_sequence: int,
    kv_bytes: float,
    score_bytes: float,
) -> dict:
    numeric = (
        parameters_billions,
        weight_bytes,
        layers,
        attention_heads,
        kv_heads,
        head_dim,
        sequences,
        tokens_per_sequence,
        kv_bytes,
        score_bytes,
    )
    if any(not math.isfinite(value) or value <= 0 for value in numeric):
        raise ValueError("all model and workload values must be positive")
    if kv_heads > attention_heads:
        raise ValueError("kv_heads cannot exceed attention_heads")
    total_tokens = sequences * tokens_per_sequence
    weight_total = parameters_billions * 1_000_000_000 * weight_bytes
    kv_total = 2 * layers * total_tokens * kv_heads * head_dim * kv_bytes
    score_elements = sequences * attention_heads * tokens_per_sequence**2
    score_total = score_elements * score_bytes
    return {
        "assumptions": {
            "parameters_billions": parameters_billions,
            "weight_bytes": weight_bytes,
            "layers": layers,
            "attention_heads": attention_heads,
            "kv_heads": kv_heads,
            "head_dim": head_dim,
            "sequences": sequences,
            "tokens_per_sequence": tokens_per_sequence,
            "kv_bytes": kv_bytes,
            "score_bytes": score_bytes,
        },
        "weights_gib": weight_total / GIB,
        "kv_cache_gib": kv_total / GIB,
        "conceptual_attention_score_elements_per_layer": score_elements,
        "attention_scores_gib_per_layer_if_materialized": score_total / GIB,
        "limits": [
            "Weight size excludes metadata, temporary buffers, runtime state, and allocator overhead.",
            "KV size assumes a dense fixed shape and counts populated tokens only.",
            "Attention score size is conceptual; fused kernels need not materialize the full matrix.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters-billions", type=float, default=7)
    parser.add_argument("--weight-bytes", type=float, default=2)
    parser.add_argument("--layers", type=int, default=32)
    parser.add_argument("--attention-heads", type=int, default=32)
    parser.add_argument("--kv-heads", type=int, default=32)
    parser.add_argument("--head-dim", type=int, default=128)
    parser.add_argument("--sequences", type=int, default=4)
    parser.add_argument("--tokens-per-sequence", type=int, default=4096)
    parser.add_argument("--kv-bytes", type=float, default=2)
    parser.add_argument("--score-bytes", type=float, default=2)
    args = parser.parse_args()
    try:
        report = estimate(**vars(args))
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
