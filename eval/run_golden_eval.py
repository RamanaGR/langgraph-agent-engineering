#!/usr/bin/env python3
"""Run golden-set retrieval eval against live API (local dev)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

from eval.metrics import f1_at_k, keyword_recall_at_k

ROOT = Path(__file__).resolve().parents[1]


def load_golden(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description="TalentScreen golden-set retrieval eval")
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument(
        "--golden",
        default=str(ROOT / "eval/golden_sets/phase1b.json"),
    )
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--mode", choices=["hybrid", "dense"], default="hybrid")
    parser.add_argument("--threshold", type=float, default=0.60)
    args = parser.parse_args()

    golden = load_golden(Path(args.golden))
    tenant_id = golden.get("tenant_id", "demo-tenant")
    pairs = golden["pairs"]

    f1_scores: list[float] = []
    keyword_scores: list[float] = []

    with httpx.Client(timeout=180.0) as client:
        for pair in pairs:
            payload = {
                "query": pair["query"],
                "tenant_id": tenant_id,
                "top_k": args.k,
                "generate_answer": False,
                "use_cache": False,
                "retrieval_mode": args.mode,
            }
            resp = client.post(f"{args.api}/query", json=payload)
            resp.raise_for_status()
            data = resp.json()
            retrieved_ids = [h["chunk_id"] for h in data.get("hits", [])]
            texts = [h.get("text") or "" for h in data.get("hits", [])]

            expected_ids = pair.get("expected_chunk_ids") or []
            if expected_ids:
                f1_scores.append(f1_at_k(retrieved_ids, expected_ids, args.k))
            keywords = pair.get("expected_keywords_in_chunks") or []
            keyword_scores.append(keyword_recall_at_k(texts, keywords, args.k))

    metric_name = "F1@K" if any(p.get("expected_chunk_ids") for p in pairs) else "keyword_recall@K"
    scores = f1_scores if f1_scores else keyword_scores
    avg = sum(scores) / len(scores) if scores else 0.0

    print(f"Golden set: {Path(args.golden).name}")
    print(f"Mode: {args.mode} | Queries: {len(pairs)} | Metric: {metric_name}")
    print(f"Average {metric_name}: {avg:.3f} (threshold >= {args.threshold})")

    if avg < args.threshold:
        print("FAIL: below threshold", file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
