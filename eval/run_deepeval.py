#!/usr/bin/env python3
"""DeepEval quality gates for RAG answers (requires LLM — Ollama or cloud)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]

THRESHOLDS = {
    "faithfulness": 0.75,
    "contextual_recall": 0.70,
    "answer_relevance": 0.70,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="TalentScreen DeepEval gate")
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument(
        "--golden",
        default=str(ROOT / "eval/golden_sets/phase1b.json"),
    )
    parser.add_argument("--limit", type=int, default=5, help="Max pairs to score (cost control)")
    args = parser.parse_args()

    try:
        from deepeval import evaluate
        from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
        from deepeval.test_case import LLMTestCase
    except ImportError:
        print("Install eval extras: uv sync --extra eval", file=sys.stderr)
        return 1

    if (
        not os.environ.get("OPENAI_API_KEY")
        and os.environ.get("LLM_PROVIDER", "ollama") == "ollama"
    ):
        print(
            "DeepEval needs a judge LLM. Set OPENAI_API_KEY or run with "
            "LLM_PROVIDER=anthropic + ANTHROPIC_API_KEY.",
            file=sys.stderr,
        )
        return 0  # soft skip for local-only dev

    golden = json.loads(Path(args.golden).read_text())
    tenant_id = golden.get("tenant_id", "demo-tenant")
    pairs = golden["pairs"][: args.limit]

    test_cases: list[LLMTestCase] = []
    with httpx.Client(timeout=180.0) as client:
        for pair in pairs:
            resp = client.post(
                f"{args.api}/query",
                json={
                    "query": pair["query"],
                    "tenant_id": tenant_id,
                    "top_k": 5,
                    "generate_answer": True,
                    "use_cache": False,
                    "retrieval_mode": "hybrid",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            contexts = [h.get("text") or "" for h in data.get("hits", [])]
            answer = (data.get("answer") or {}).get("answer", "")
            test_cases.append(
                LLMTestCase(
                    input=pair["query"],
                    actual_output=answer,
                    retrieval_context=contexts,
                )
            )

    metrics = [
        FaithfulnessMetric(threshold=THRESHOLDS["faithfulness"]),
        AnswerRelevancyMetric(threshold=THRESHOLDS["answer_relevance"]),
    ]
    evaluate(test_cases=test_cases, metrics=metrics)
    print("DeepEval completed — see report above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
