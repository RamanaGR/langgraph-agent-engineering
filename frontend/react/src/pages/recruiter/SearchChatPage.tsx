import { useState } from "react";
import { api, type QueryHit, type RankedCandidate } from "../../api/client";
import { CandidateFitCards } from "../../components/CandidateFitCards";
import { MarkdownMessage } from "../../components/MarkdownMessage";

interface ChatMessage {
  role: "user" | "agent";
  text: string;
  rankedCandidates?: RankedCandidate[];
  noMatch?: boolean;
}

export function SearchChatPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"search" | "agent">("search");
  const [retrievalMode, setRetrievalMode] = useState("hybrid");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hits, setHits] = useState<QueryHit[]>([]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [rewrites, setRewrites] = useState<string[]>([]);
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const [threadId, setThreadId] = useState<string | undefined>();

  const runSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.query(query, retrievalMode);
      setHits(res.hits);
      setAnswer(res.answer?.answer || null);
      setRewrites(res.rewritten_queries || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const runAgent = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    const userMsg = query;
    setChatLog((prev) => [...prev, { role: "user", text: userMsg }]);
    setQuery("");
    try {
      const res = await api.agentChat(userMsg, threadId);
      setThreadId(res.thread_id);
      const fit = res.task_results?.candidate_fit;
      const ranked = fit?.ranked_candidates ?? [];
      const agentText =
        res.response ||
        (res.interrupted
          ? "Awaiting recruiter approval — check the Approvals inbox."
          : "No response generated.");
      setChatLog((prev) => [
        ...prev,
        {
          role: "agent",
          text: agentText,
          rankedCandidates: ranked.length > 0 ? ranked : undefined,
          noMatch: fit?.no_strong_matches,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent chat failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "search") runSearch();
    else runAgent();
  };

  return (
    <>
      <h1 className="page-title">Candidate Search & Agent Chat</h1>
      <p className="page-subtitle">
        Hybrid RAG search or multi-agent chat for hiring decisions.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
          <button
            type="button"
            className={mode === "search" ? "" : "secondary"}
            onClick={() => setMode("search")}
          >
            RAG Search
          </button>
          <button
            type="button"
            className={mode === "agent" ? "" : "secondary"}
            onClick={() => setMode("agent")}
          >
            Agent Chat
          </button>
        </div>

        {mode === "search" && (
          <>
            <label>Retrieval mode</label>
            <select value={retrievalMode} onChange={(e) => setRetrievalMode(e.target.value)}>
              <option value="hybrid">Hybrid (BM25 + dense)</option>
              <option value="dense">Dense only</option>
            </select>
          </>
        )}

        <form onSubmit={handleSubmit}>
          <label>{mode === "search" ? "Search query" : "Message"}</label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              mode === "search"
                ? "Who has Java and AWS experience?"
                : "Who has AI/ML experience with min 2 years?"
            }
          />
          <button type="submit" disabled={loading || !query.trim()}>
            {loading ? "Running…" : mode === "search" ? "Search" : "Send"}
          </button>
        </form>
      </div>

      {mode === "agent" && chatLog.length > 0 && (
        <div className="card">
          <h3>Conversation</h3>
          <div className="chat-log">
            {chatLog.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.role}`}>
                {msg.role === "user" ? (
                  msg.text
                ) : (
                  <>
                    {msg.rankedCandidates && msg.rankedCandidates.length > 0 && (
                      <CandidateFitCards candidates={msg.rankedCandidates} />
                    )}
                    {msg.noMatch && (
                      <div className="no-match-banner">No strong matches for your criteria</div>
                    )}
                    <MarkdownMessage content={msg.text} />
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {mode === "search" && rewrites.length > 0 && (
        <div className="card">
          <h3>LLM query rewrites</h3>
          <ul className="hit-list">
            {rewrites.map((q, i) => (
              <li key={i} className="hit-item">
                {q}
              </li>
            ))}
          </ul>
        </div>
      )}

      {mode === "search" && answer && (
        <div className="card">
          <h3>Answer</h3>
          <MarkdownMessage content={answer} />
        </div>
      )}

      {mode === "search" && hits.length > 0 && (
        <div className="card">
          <h3>Retrieved chunks ({hits.length})</h3>
          <ul className="hit-list">
            {hits.map((hit) => (
              <li key={hit.chunk_id} className="hit-item">
                <div className="hit-meta">
                  {hit.doc_type} · score {hit.score.toFixed(3)} · {hit.chunk_id.slice(0, 8)}…
                </div>
                {hit.text}
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}
