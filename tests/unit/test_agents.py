"""Phase 2a — LangGraph agent unit tests."""

from talentscreen.agents.nodes._helpers import classify_intent_rules
from talentscreen.agents.nodes.dispatch import dispatch_route
from talentscreen.agents.tools.guardrails import guardrails_check
from talentscreen.agents.tools.postgres import postgres_query


def test_classify_hiring_intent() -> None:
    assert classify_intent_rules("Who has Java and AWS experience?") == "hiring"


def test_classify_scheduling_intent() -> None:
    assert classify_intent_rules("Schedule an interview slot for tomorrow") == "scheduling"


def test_dispatch_routes_to_retrieval_first() -> None:
    state = {
        "execution_plan": [
            {"agent": "retrieval", "status": "pending", "description": ""},
            {"agent": "bias_fairness", "status": "pending", "description": ""},
        ]
    }
    assert dispatch_route(state) == "retrieval"


def test_dispatch_aggregate_when_done() -> None:
    state = {
        "execution_plan": [
            {"agent": "retrieval", "status": "done", "description": ""},
        ]
    }
    assert dispatch_route(state) == "aggregate"


def test_postgres_query_blocks_insert() -> None:
    result = postgres_query.invoke(
        {
            "sql": "INSERT INTO candidates (full_name) VALUES ('x')",
            "tenant_id": "demo-tenant",
        }
    )
    assert "error" in result


def test_postgres_query_requires_tenant_filter() -> None:
    result = postgres_query.invoke(
        {"sql": "SELECT * FROM candidates", "tenant_id": "demo-tenant"}
    )
    assert "tenant_id" in result.get("error", "")


def test_guardrails_flags_bias() -> None:
    result = guardrails_check.invoke({"text": "We need a young rockstar ninja developer"})
    assert result["passed"] is False
    assert "biased_language" in result["issues"]


def test_build_agent_graph_compiles() -> None:
    from talentscreen.agents.graph import build_agent_graph

    graph = build_agent_graph()
    assert graph is not None
