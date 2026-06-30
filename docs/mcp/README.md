# TalentScreen MCP servers (Phase 2b)

Thin wrappers over verified native `@tool` functions — **zero logic duplication**.

## Servers

| Server | Command | Wraps |
|--------|---------|-------|
| `talentscreen-rag` | `uv run talentscreen-mcp-rag` | `agents.tools.rag.rag_retrieve` |
| `talentscreen-postgres` | `uv run talentscreen-mcp-postgres` | `agents.tools.postgres.postgres_query` |

## Cursor / Claude Desktop config

Add to your MCP settings (stdio transport):

```json
{
  "mcpServers": {
    "talentscreen-rag": {
      "command": "uv",
      "args": ["run", "talentscreen-mcp-rag"],
      "cwd": "/path/to/langgraph-agent-engineering-1"
    },
    "talentscreen-postgres": {
      "command": "uv",
      "args": ["run", "talentscreen-mcp-postgres"],
      "cwd": "/path/to/langgraph-agent-engineering-1"
    }
  }
}
```

Ensure Docker (Postgres, Milvus, Redis) and Ollama are running before using the RAG server.

## Equivalence test (native @tool vs MCP wrapper)

```bash
uv run python eval/run_mcp_equivalence.py
# or
curl http://localhost:8000/mcp/equivalence
```

Interview talking point: *"`@tool` functions are verified first; MCP servers in `src/talentscreen/mcp/` delegate to the same code — no duplicated business logic."*
