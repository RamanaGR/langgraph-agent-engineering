# Phase 2 — Multi-agent LangGraph

## Graph topology

```
Router → Summarize? → Orchestrator (plan) → Dispatch:
  Retrieval → ResumeAnalysis → CandidateFit → BiasFairness → ConversationManager
→ Orchestrator (aggregate) → HITL → Response
```

Compile: `src/talentscreen/agents/graph.py`.

## Agent responsibilities

| Node | File | Resume capability |
|------|------|-------------------|
| RouterAgent | `router.py` | Routing |
| OrchestratorAgent | `orchestrator.py` | Orchestration |
| RetrievalAgent | `retrieval.py` | Retrieval + rewrite |
| ResumeAnalysisAgent | `resume_analysis.py` | Candidate matching |
| CandidateFitAgent | `candidate_fit.py` | Fit scoring + interview Qs |
| ConversationManagerAgent | `conversation_manager.py` | Dialogue continuity |
| BiasFairnessAgent | `bias_fairness.py` | Guardrails |

## Tools and MCP

- Native: `rag_retrieve`, `postgres_query`, `guardrails_check` in `agents/tools/`.
- MCP: `uv run talentscreen-mcp-rag`, `uv run talentscreen-mcp-postgres`.

## HITL

High-impact recommendations pause at `hitl_gate_node`. Resume via:

```bash
curl -X POST localhost:8000/agents/resume/{thread_id} \
  -H 'Content-Type: application/json' -d '{"action":"approve"}'
```

React Approvals inbox: `/recruiter/approvals`.

## State

`AgentState` in `agents/state.py` — messages, intent, execution_plan, retrieved_context, rewritten_queries, pending_approval.

Checkpointer: `AGENT_CHECKPOINTER=postgres` for durable threads.
