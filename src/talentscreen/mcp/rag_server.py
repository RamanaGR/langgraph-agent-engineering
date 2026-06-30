"""MCP rag-server — wraps agents.tools.rag.rag_retrieve."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from talentscreen.mcp.wrappers import mcp_rag_retrieve

mcp = FastMCP(
    "talentscreen-rag",
    instructions="Hybrid RAG retrieval over resumes, job descriptions, and interview notes.",
)


@mcp.tool()
def rag_retrieve(
    query: str,
    tenant_id: str = "demo-tenant",
    top_k: int = 5,
    retrieval_mode: str = "hybrid",
) -> dict:
    """Retrieve relevant hiring document chunks via hybrid dense+BM25 RAG."""
    return mcp_rag_retrieve(
        query=query,
        tenant_id=tenant_id,
        top_k=top_k,
        retrieval_mode=retrieval_mode,
    )


def main() -> None:
    mcp.run()
