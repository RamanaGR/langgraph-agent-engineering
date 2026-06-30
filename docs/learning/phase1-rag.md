# Phase 1 — RAG fundamentals

## Docling vs Unstructured

- **Docling**: PDF/DOCX with layout — tables and headers preserved for resume parsing.
- **Unstructured**: md/txt/logs — fast text cleanup for interview notes and JD markdown.

Router: `src/talentscreen/ingestion/router.py`.

## Chunking and indexing

- Semantic chunks with overlap (`chunk_size=512`, `overlap=64`).
- Postgres stores canonical text; Milvus stores vectors keyed by `chunk_id`.

## Retrieval pipeline (1a → 1b)

1. Presidio PII redaction
2. LLM query rewrite (mandatory in 1b) — 2–3 variants
3. Exact + semantic Redis cache
4. Hybrid BM25 + dense with RRF fusion
5. Cross-encoder rerank
6. LLM answer with citation validation

## Evaluation

- Golden sets: `eval/golden_sets/phase1b.json` (45 queries)
- F1@5 threshold ≥ 0.60
- Promptfoo: `cd eval/promptfoo && npx promptfoo eval`
- DeepEval: faithfulness, context recall, answer relevance

## Try it

```bash
docker compose up -d
uv run talentscreen-api
./scripts/seed_synthetic_data.sh
curl -X POST localhost:8000/query -H 'Content-Type: application/json' \
  -d '{"query":"Who has Java and AWS?","retrieval_mode":"hybrid"}'
```
