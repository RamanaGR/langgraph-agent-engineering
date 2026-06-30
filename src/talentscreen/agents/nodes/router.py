"""RouterAgent — classify intent and reject out-of-scope requests."""

from __future__ import annotations

import json

from talentscreen.agents.nodes._helpers import classify_intent_rules, last_user_message
from talentscreen.agents.state import AgentState
from talentscreen.generation.citations import parse_llm_json
from talentscreen.generation.llm.provider import get_llm_provider


def _llm_classify(text: str) -> str | None:
    try:
        llm = get_llm_provider()
        response = llm.invoke(
            [
                {
                    "role": "system",
                    "content": (
                        "Classify recruiter intent. JSON only: "
                        '{"intent": "hiring|policy|scheduling|out_of_scope"}'
                    ),
                },
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
        )
        payload = parse_llm_json(response.content)
        intent = str(payload.get("intent", "")).strip()
        if intent in ("hiring", "policy", "scheduling", "out_of_scope"):
            return intent
    except (json.JSONDecodeError, TypeError, ValueError, OSError):
        return None
    return None


def router_node(state: AgentState) -> dict:
    query = last_user_message(state)
    intent = _llm_classify(query) or classify_intent_rules(query)
    return {
        "intent": intent,
        "user_query": query,
        "tenant_id": state.get("tenant_id") or "demo-tenant",
    }
