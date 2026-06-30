# Resume justification — module → bullet mapping

Use this doc in interviews to point reviewers to **real code** for each resume bullet.

| Resume bullet | Demo path | What to show |
|---------------|-----------|--------------|
| AI talent platform (RAG + multi-agent) | `frontend/react/` + `/agents/chat` | End-to-end recruiter UI → agent graph |
| LangGraph specialized agents | `src/talentscreen/agents/nodes/` | 7 files: router, orchestrator, retrieval, resume_analysis, candidate_fit, conversation_manager, bias_fairness |
| MCP tool infrastructure | `src/talentscreen/mcp/` | `talentscreen-mcp-rag`, `talentscreen-mcp-postgres`, equivalence test |
| Unstructured.io + Docling ingestion | `src/talentscreen/ingestion/router.py` | PDF/DOCX → Docling; md/txt → Unstructured |
| Semantic chunking + embeddings | `ingestion/chunking.py`, `generation/embeddings/` | Overlap chunking; Ollama/ST locally, Titan via Bedrock stub |
| Milvus hybrid + HNSW | `retrieval/milvus/`, `retrieval/hybrid.py` | Dense + BM25 RRF fusion |
| Cross-encoder reranking + F1@K | `retrieval/rerank.py`, `eval/metrics.py` | `run_golden_eval.py --mode hybrid` |
| Query rewriting + Presidio | `retrieval/query_rewrite.py`, `guardrails/pii.py` | Rewrites in `/query` response; PII in pipeline |
| Redis semantic query cache | `retrieval/semantic_cache.py` | `cache_type: semantic` in API response |
| Prompting + Promptfoo | `eval/promptfoo/promptfoo.yaml` | `npx promptfoo eval` |
| Bedrock Claude + prompt cache | `generation/llm/bedrock_stub.py` | Typed interface; swap `LLM_PROVIDER` |
| CI/CD DeepEval | `.github/workflows/eval.yml` | F1@K unit gates + golden set schema |
| Guardrails (PII, bias, toxicity) | `agents/nodes/bias_fairness.py` | BiasFairnessAgent + `guardrails_check` tool |
| React full stack | `frontend/react/` | Recruiter upload/search/HITL + candidate apply/status |
| Langfuse observability | `observability/langfuse_tracer.py` | Traces on `/query` when keys set |

## 60-second pitch

"We built TalentScreen as a local-first hiring platform: Docling and Unstructured ingest resumes into Postgres and Milvus; hybrid retrieval with mandatory LLM query rewrite feeds a LangGraph workflow with seven resume-aligned agents. Recruiters use React for upload, RAG search, agent chat, and HITL approvals; candidates apply through the same API. MCP wrappers prove tool equivalence for external integrations. Terraform in `infra/aws/` documents the AWS swap without requiring credentials for the demo."
