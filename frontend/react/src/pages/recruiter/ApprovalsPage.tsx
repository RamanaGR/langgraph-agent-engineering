import { useCallback, useEffect, useState } from "react";
import { api, type PendingApproval } from "../../api/client";

export function ApprovalsPage() {
  const [items, setItems] = useState<PendingApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acting, setActing] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const pending = await api.listPending();
      setItems(pending);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load approvals");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleAction = async (threadId: string, action: "approve" | "reject") => {
    setActing(threadId);
    try {
      await api.resumeAgent(threadId, action);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setActing(null);
    }
  };

  return (
    <>
      <h1 className="page-title">Approval Inbox (HITL)</h1>
      <p className="page-subtitle">
        Review high-impact agent recommendations before they are finalized.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <div style={{ marginBottom: "1rem" }}>
        <button type="button" className="secondary" onClick={load} disabled={loading}>
          Refresh
        </button>
      </div>

      {loading && <p style={{ color: "var(--muted)" }}>Loading…</p>}

      {!loading && items.length === 0 && (
        <div className="card">
          <p style={{ margin: 0, color: "var(--muted)" }}>
            No pending approvals. Run an agent chat that triggers HITL (e.g. candidate
            shortlist recommendation).
          </p>
        </div>
      )}

      {items.map((item) => (
        <div key={item.thread_id} className="card">
          <div className="hit-meta">Thread {item.thread_id}</div>
          {item.preview && <p>{item.preview}</p>}
          <pre
            style={{
              fontSize: "0.8rem",
              background: "var(--bg)",
              padding: "0.75rem",
              borderRadius: 8,
              overflow: "auto",
            }}
          >
            {JSON.stringify(item.pending_approval, null, 2)}
          </pre>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
            <button
              onClick={() => handleAction(item.thread_id, "approve")}
              disabled={acting === item.thread_id}
            >
              Approve
            </button>
            <button
              className="danger"
              onClick={() => handleAction(item.thread_id, "reject")}
              disabled={acting === item.thread_id}
            >
              Reject
            </button>
          </div>
        </div>
      ))}
    </>
  );
}
