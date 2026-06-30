"""Compile the 7-agent LangGraph hiring workflow."""

from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from talentscreen.agents.nodes.bias_fairness import bias_fairness_node
from talentscreen.agents.nodes.candidate_fit import candidate_fit_node
from talentscreen.agents.nodes.conversation_manager import conversation_manager_node
from talentscreen.agents.nodes.dispatch import dispatch_route, reject_node
from talentscreen.agents.nodes.hitl import hitl_gate_node
from talentscreen.agents.nodes.orchestrator import (
    orchestrator_aggregate_node,
    orchestrator_plan_node,
)
from talentscreen.agents.nodes.resume_analysis import resume_analysis_node
from talentscreen.agents.nodes.retrieval import retrieval_node
from talentscreen.agents.nodes.router import router_node
from talentscreen.agents.nodes.summarization import should_summarize, summarization_node
from talentscreen.agents.state import AgentState

_AGENT_NODES = {
    "retrieval": "retrieval",
    "resume_analysis": "resume_analysis",
    "candidate_fit": "candidate_fit",
    "conversation_manager": "conversation_manager",
    "bias_fairness": "bias_fairness",
}


def _after_router(state: AgentState) -> str:
    if state.get("intent") == "out_of_scope":
        return "reject"
    return should_summarize(state)


def build_agent_graph(checkpointer: BaseCheckpointSaver | None = None):
    builder = StateGraph(AgentState)

    builder.add_node("router", router_node)
    builder.add_node("summarization", summarization_node)
    builder.add_node("orchestrator_plan", orchestrator_plan_node)
    builder.add_node("dispatch", lambda state: {})
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("resume_analysis", resume_analysis_node)
    builder.add_node("candidate_fit", candidate_fit_node)
    builder.add_node("conversation_manager", conversation_manager_node)
    builder.add_node("bias_fairness", bias_fairness_node)
    builder.add_node("orchestrator_aggregate", orchestrator_aggregate_node)
    builder.add_node("hitl_gate", hitl_gate_node)
    builder.add_node("reject", reject_node)

    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        _after_router,
        {
            "reject": "reject",
            "summarize": "summarization",
            "skip": "orchestrator_plan",
        },
    )
    builder.add_edge("summarization", "orchestrator_plan")
    builder.add_edge("orchestrator_plan", "dispatch")

    dispatch_targets = {**_AGENT_NODES, "aggregate": "orchestrator_aggregate", "reject": "reject"}
    builder.add_conditional_edges("dispatch", dispatch_route, dispatch_targets)

    for agent in _AGENT_NODES:
        builder.add_edge(agent, "dispatch")

    builder.add_edge("orchestrator_aggregate", "hitl_gate")
    builder.add_edge("hitl_gate", END)
    builder.add_edge("reject", END)

    saver = checkpointer or MemorySaver()
    return builder.compile(checkpointer=saver)
