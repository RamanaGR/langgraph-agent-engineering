# Phase 3 — Production UI, auth, Terraform

## React frontend

Location: `frontend/react/`

| Route | Audience | API |
|-------|----------|-----|
| `/recruiter/upload` | Recruiter | `POST /ingest` |
| `/recruiter/search` | Recruiter | `POST /query`, `POST /agents/chat` |
| `/recruiter/approvals` | Recruiter | `GET /agents/pending`, `POST /agents/resume/{id}` |
| `/candidate/jobs` | Candidate | `GET /jobs` |
| `/candidate/apply/:jobId` | Candidate | `POST /applications` |
| `/candidate/status` | Candidate | `GET /applications/{id}` |

### Run locally

```bash
# Terminal 1 — API (with CORS for :5173)
uv run talentscreen-api

# Terminal 2 — React
cd frontend/react
npm install
npm run dev
```

Vite proxies `/api/*` → `http://localhost:8000`.

## Auth

Set in `.env`:

```
AUTH_ENABLED=true
API_KEY_RECRUITER=your-recruiter-key
API_KEY_CANDIDATE=your-candidate-key
CORS_ORIGINS=http://localhost:5173
```

React sends `X-API-Key` and `X-Role` on every request. When `AUTH_ENABLED=false` (default), keys are optional for local dev.

## API guardrails

- **Prompt injection**: `assert_safe_prompt()` on `/query` and `/agents/chat`.
- **PII / bias**: Presidio in RAG pipeline; BiasFairnessAgent in graph.

## Terraform

Reference IaC: `infra/aws/`. See [aws-mapping.md](../aws-mapping.md).

Files: `s3.tf`, `lambda_ingest.tf`, `api_gateway.tf`, `bedrock_iam.tf`, `rds.tf`, `elasticache.tf`, `secrets_manager.tf`, `eks_milvus/`.

## CI eval gates

- `ci.yml` — lint + unit tests
- `eval.yml` — F1@K metric tests + golden set schema (40+ pairs)

Full integration eval requires Docker + Ollama (`workflow_dispatch`).
