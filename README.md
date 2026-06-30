# TalentScreen

Local RAG + LangGraph multi-agent hiring platform (portfolio build).

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for architecture and phased roadmap.

## Week 1 — Quick start

### Prerequisites

- Docker Desktop
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Ollama with `llama3.2:latest` + `nomic-embed-text:latest`

### 1. Environment

```bash
cp .env.example .env
uv sync --extra dev
# Optional Docling for PDF/DOCX parsing:
uv sync --extra docling
```

### 2. Start infrastructure

```bash
docker compose up -d
```

Services: Postgres `5432`, Redis `6379`, MinIO `9000` (console `9001`), Milvus `19530`, Langfuse `3000`.

### 3. Run API + ingestion worker (two terminals)

```bash
uv run talentscreen-api
```

```bash
uv run talentscreen-worker
```

### 4. Health check

```bash
curl http://localhost:8000/health
curl http://localhost:8000/degraded
```

### 5. Seed synthetic data

```bash
chmod +x scripts/seed_synthetic_data.sh
./scripts/seed_synthetic_data.sh
```

### 6. Query (after ingestion completes)

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "Who has Java and AWS experience?", "top_k": 5, "generate_answer": true}'
```

Response includes: PII scan, query expansion, dense + reranked hits (with text), LLM answer + validated citations, cache status.

## Week 2 — RAG pipeline + debug UI

Phase 1a completion: Presidio PII → rule-based expansion → Redis exact cache → Milvus dense → cross-encoder rerank → LLM answer with citations → Langfuse trace (optional).

### Streamlit debug UI

```bash
uv run talentscreen-debug
# Opens http://localhost:8501 — shows dense scores, rerank order, citations
```

### Optional: Langfuse tracing

Set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `.env` (Langfuse runs at `http://localhost:3000` via docker compose).

### Optional: Presidio (full PII)

```bash
python -m spacy download en_core_web_lg
```

Without spaCy, regex fallback redacts emails/phones/SSNs.

## Phase 2a — LangGraph 7-agent graph

Seven resume-aligned agent nodes + SummarizationNode, native `@tool` functions, HITL interrupt.

```
Router → Summarize? → Orchestrator (plan) → Dispatch loop:
  Retrieval → ResumeAnalysis → CandidateFit → BiasFairness → ConversationManager
→ Orchestrator (aggregate) → HITL gate → Response
```

### Agent chat API

```bash
curl -X POST http://localhost:8000/agents/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Who best matches Java and AWS for the Senior Java role?"}'
```

HITL resume (after `interrupted: true`):

```bash
curl -X POST http://localhost:8000/agents/resume/{thread_id} \
  -H 'Content-Type: application/json' \
  -d '{"action": "approve"}'
```

### Agent files (demo paths)

| Agent | File |
|-------|------|
| Router | `src/talentscreen/agents/nodes/router.py` |
| Orchestrator | `src/talentscreen/agents/nodes/orchestrator.py` |
| Retrieval | `src/talentscreen/agents/nodes/retrieval.py` |
| Resume analysis | `src/talentscreen/agents/nodes/resume_analysis.py` |
| Candidate fit | `src/talentscreen/agents/nodes/candidate_fit.py` |
| Conversation | `src/talentscreen/agents/nodes/conversation_manager.py` |
| Bias / fairness | `src/talentscreen/agents/nodes/bias_fairness.py` |

Set `AGENT_CHECKPOINTER=postgres` for durable threads (uses same Postgres as app).

## Phase 2b — MCP wrappers

Thin MCP servers delegate to native `@tool` functions (no logic rewrite).

```bash
uv run talentscreen-mcp-rag        # stdio MCP — hybrid RAG
uv run talentscreen-mcp-postgres   # stdio MCP — read-only SQL + RBAC
```

Equivalence demo (native vs MCP wrapper):

```bash
uv run python eval/run_mcp_equivalence.py
curl http://localhost:8000/mcp/equivalence
```

See [docs/mcp/README.md](docs/mcp/README.md) for Cursor MCP config.

## Phase 1b — Hybrid search + LLM rewrite + eval

```
Query → PII → LLM rewrite (2–3 variants) → semantic cache?
  → dense (per variant) + BM25 → RRF fusion → rerank → answer
```

### Query with hybrid mode

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Who has Java and AWS experience?",
    "top_k": 5,
    "retrieval_mode": "hybrid",
    "generate_answer": true,
    "use_cache": false
  }'
```

Response adds `rewritten_queries`, `fused_hit_count`, `cache_type` (`exact` | `semantic`).

### Golden-set retrieval eval

```bash
uv run python eval/run_golden_eval.py --mode hybrid
uv run python eval/run_golden_eval.py --mode dense   # compare F1 / keyword recall
```

Golden set: `eval/golden_sets/phase1b.json` (45 queries).

### Promptfoo (prompt variants)

```bash
cd eval/promptfoo
npx promptfoo eval
npx promptfoo view
```

### DeepEval (optional — needs judge LLM API key)

```bash
uv sync --extra eval
uv run python eval/run_deepeval.py --limit 5
```

### 7. Tests

```bash
uv run pytest tests/unit -q
uv run ruff check src tests
```

## Phase 3 — React UI + auth + Terraform

Recruiter and candidate portals, API auth, and AWS reference IaC.

### React frontend

```bash
# API (terminal 1)
uv run talentscreen-api

# UI (terminal 2)
cd frontend/react
npm install
npm run dev
# → http://localhost:5173
```

| Portal | Routes |
|--------|--------|
| Recruiter | `/recruiter/upload`, `/recruiter/search`, `/recruiter/approvals` |
| Candidate | `/candidate/jobs`, `/candidate/apply/:jobId`, `/candidate/status` |

Vite proxies `/api` → FastAPI. Set `CORS_ORIGINS=http://localhost:5173` in `.env`.

### Auth (optional)

```bash
AUTH_ENABLED=true
API_KEY_RECRUITER=recruiter-dev-key
API_KEY_CANDIDATE=candidate-dev-key
```

React sends `X-API-Key` + `X-Role`. Injection heuristics block unsafe prompts on `/query` and `/agents/chat`.

### Jobs & applications API

```bash
curl http://localhost:8000/jobs -H 'X-Role: recruiter'
curl -X POST http://localhost:8000/applications \
  -F job_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -F full_name=Jane Doe -F email=jane@example.com \
  -H 'X-Role: candidate' -H 'X-API-Key: candidate-dev-key'
```

### Terraform (AWS reference — not applied locally)

See `infra/aws/README.md` and `docs/aws-mapping.md`.

### Interview docs

- `docs/resume-justification.md` — bullet → file mapping
- `docs/narrative-alignment.md` — common interview Q&A
- `docs/learning/` — phase guides

## Project layout

```
src/talentscreen/
  api/           FastAPI (/ingest, /query, /health, /degraded)
  ingestion/     File router, Docling/Unstructured, ARQ worker, MinIO
  retrieval/     Milvus dense, rerank, Redis cache, query expansion
  generation/    LLM + embeddings, RAG answers, citation validation
  guardrails/    Presidio PII redaction
  agents/        LangGraph 7-agent graph + native tools
  mcp/           MCP server wrappers (Phase 2b)
  debug/         Streamlit RAG debug UI
  observability/ Langfuse tracing
frontend/react/  Recruiter + candidate React UI (Phase 3)
infra/aws/       Terraform AWS reference (Phase 3)
docs/            aws-mapping, resume-justification, learning guides
eval/golden_sets/phase1a.json
data/synthetic/  Demo resumes, JD, interview notes
infra/sql/       Postgres schema
```

## LLM provider swap

```bash
# Local (default)
LLM_PROVIDER=ollama OLLAMA_MODEL=llama3.2:latest

# Dev escape hatch
LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=...
LLM_PROVIDER=groq GROQ_API_KEY=...
```

Production maps to **Amazon Bedrock Claude** via `src/talentscreen/generation/llm/bedrock_stub.py`.
