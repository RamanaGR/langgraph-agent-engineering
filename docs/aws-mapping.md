# AWS mapping — local demo to production

TalentScreen runs locally via Docker Compose for development and demos. This document describes how each component maps to AWS for a production deployment.

## Architecture swap

```
Local (docker compose)              AWS (Terraform in infra/aws/)
─────────────────────              ─────────────────────────────
FastAPI :8000                  →   API Gateway + ECS/EKS service
MinIO talentscreen-docs        →   S3 bucket + event → Lambda ingest
ARQ worker                     →   Lambda or ECS task (same pipeline code)
Postgres :5432                 →   RDS PostgreSQL 16
Redis :6379                    →   ElastiCache Redis 7
Milvus :19530                  →   Milvus Helm chart on EKS
Ollama llama3.2                →   Bedrock Claude Sonnet
nomic-embed-text / ST          →   Amazon Titan Text Embeddings
Langfuse :3000                 →   Langfuse Cloud or self-hosted on ECS
Streamlit debug                →   Internal ops tool (not customer-facing)
React :5173                    →   S3 + CloudFront static hosting
```

## Configuration changes for AWS

| Env var (local) | Production value |
|-----------------|------------------|
| `LLM_PROVIDER=ollama` | `LLM_PROVIDER=bedrock` |
| `EMBEDDING_PROVIDER=ollama` | Titan via Bedrock or `local` with Titan API |
| `DATABASE_URL` | From Secrets Manager `talentscreen/prod/database` |
| `REDIS_URL` | `redis://<elasticache-endpoint>:6379/0` |
| `MINIO_*` | Remove; use IAM role + S3 bucket |
| `MILVUS_HOST` | EKS service `milvus.milvus.svc.cluster.local` |
| `AUTH_ENABLED=true` | API keys in Secrets Manager |

## Data flow (production ingest)

1. Recruiter uploads via React → API Gateway → FastAPI (or presigned S3 URL).
2. S3 `ObjectCreated` triggers Lambda running the same `ingestion/pipeline.py` logic.
3. Chunks written to RDS; embeddings to Milvus on EKS.
4. Query path unchanged: hybrid retrieval → rerank → Bedrock generation.

## IAM boundaries

- **Ingest Lambda**: read S3, write RDS, call embedding endpoint, Secrets Manager read.
- **API service role**: Bedrock invoke, RDS, Redis, Milvus network access.
- **Candidate vs recruiter**: `X-API-Key` at API Gateway usage plan level (MVP); Cognito for production hardening.

## What stays the same

- LangGraph agent topology (7 nodes + SummarizationNode).
- Postgres as canonical chunk store; Milvus keyed by `chunk_id`.
- Native `@tool` functions; MCP wrappers optional on ECS.
- Eval gates (F1@K, DeepEval) in CI before deploy.
