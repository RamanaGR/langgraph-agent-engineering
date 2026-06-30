# Architecture

TalentScreen is a hiring intelligence platform: ingest resumes and job documents, run hybrid RAG retrieval, and orchestrate LangGraph agents for recruiter search, candidate fit scoring, and human-in-the-loop approvals.

## System overview

```
Documents (PDF/DOCX/txt) → Ingestion → Postgres (chunks) + Milvus (vectors)
                                              ↓
Recruiter query → PII guard → LLM query rewrite → hybrid retrieval → rerank → cited answer
                                              ↓
Agent chat → Router → Orchestrator → specialized agents → HITL gate → response
```

## Tech stack

| Layer | Components |
|-------|------------|
| API | FastAPI, async SQLAlchemy, ARQ worker |
| Storage | Postgres (metadata + chunks), MinIO (objects), Milvus (vectors), Redis (cache + queue) |
| Retrieval | Dense search, BM25, RRF fusion, cross-encoder rerank, semantic cache |
| Generation | Ollama (local) or Bedrock stub (production path) |
| Agents | LangGraph — 7 agent nodes + SummarizationNode |
| UI | React (recruiter + candidate), Streamlit (RAG debug) |
| Observability | Langfuse (optional) |
| IaC | Terraform reference in `infra/aws/` |

## Agent graph

```
Router → Summarize? → Orchestrator (plan) → Dispatch loop:
  Retrieval → ResumeAnalysis → CandidateFit → BiasFairness → ConversationManager
→ Orchestrator (aggregate) → HITL gate → Response
```

| Agent | Responsibility |
|-------|----------------|
| Router | Classify intent; route or reject out-of-scope requests |
| Orchestrator | Build execution plan, delegate sub-goals, aggregate results |
| Retrieval | LLM query rewrite, hybrid RAG, rerank, package context |
| Resume analysis | Normalize skills and experience; compare candidates |
| Candidate fit | Score against job description; surface gaps and interview questions |
| Conversation manager | Dialogue continuity and clarifying questions |
| Bias / fairness | PII and biased-language checks on outputs |

**SummarizationNode** compresses conversation history when message count exceeds the configured threshold.

## State management

| Concern | Owner |
|---------|-------|
| Execution plan, messages, retrieved context | LangGraph State + Postgres checkpointer |
| HITL resume | Postgres checkpointer (`POST /agents/resume/{thread_id}`) |
| Query result caching | Redis |
| Ingestion jobs | Redis + ARQ worker |

## Data model

- **Postgres** is the canonical chunk store.
- **Milvus** stores embeddings keyed by `chunk_id`.
- **MinIO** holds raw uploaded documents.

## Production mapping

See [aws-mapping.md](aws-mapping.md) for how local Docker services map to AWS (S3, Lambda, RDS, ElastiCache, EKS Milvus, Bedrock).
