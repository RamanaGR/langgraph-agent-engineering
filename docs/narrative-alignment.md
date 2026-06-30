# Narrative alignment — interview answers

## Why LangGraph instead of a single RAG chain?

Recruiters don't ask one question — they compare candidates, check policy, and need explainable citations. We split concerns into **Router** (intent), **Orchestrator** (plan + aggregate), **Retrieval** (rewrite + hybrid search), **ResumeAnalysis** + **CandidateFit** (matching), **ConversationManager** (clarifications), and **BiasFairness** (guardrails). Each maps to a resume capability and a file under `agents/nodes/`.

## Why not Redis as a blackboard?

Early designs used Redis for execution state. We refactored to **LangGraph State + Postgres checkpointer** as the single blackboard to avoid dual-state bugs. Redis is only query cache (`ts:cache:*`) and the ARQ ingestion queue.

## How do you demo query rewriting?

1. POST `/query` with `retrieval_mode=hybrid` — response includes `rewritten_queries`.
2. Open Streamlit debug or React Search page.
3. Show Langfuse trace for rewrite step inside `RetrievalAgent`.

## How do you demo bias and guardrails?

Open `bias_fairness.py`. Ask the agent about a candidate; BiasFairnessAgent runs `guardrails_check` (Presidio PII + biased-language heuristics). API layer also blocks prompt injection via `guardrails/injection.py` on `/query` and `/agents/chat`.

## MCP vs native tools?

Phase 2a verified **native `@tool`** functions in `agents/tools/`. Phase 2b added thin MCP servers with **zero logic duplication** — `eval/run_mcp_equivalence.py` proves parity.

## What about Google ADK / Vertex from your earlier project narrative?

`project_info.md` describes the **Innovapath/GCP** production context. This repo is a **LangGraph + AWS-aligned portfolio build** with local equivalents. Same problems (RAG → agents → HITL), different orchestration framework for resume alignment.

## Phase 3 additions

- **React** recruiter and candidate portals (`frontend/react/`).
- **Auth**: `X-API-Key` + role headers; enable with `AUTH_ENABLED=true`.
- **Terraform** reference in `infra/aws/` for S3, Lambda, API Gateway, Bedrock IAM, RDS, ElastiCache, EKS Milvus.
