import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type ApplicationResponse } from "../../api/client";

export function StatusPage() {
  const [params] = useSearchParams();
  const initialId = params.get("id") || "";
  const [lookupId, setLookupId] = useState(initialId);
  const [email, setEmail] = useState("");
  const [application, setApplication] = useState<ApplicationResponse | null>(null);
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialId) {
      setLookupId(initialId);
      loadById(initialId);
    }
  }, [initialId]);

  const loadById = async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const app = await api.getApplication(id.trim());
      setApplication(app);
      setApplications([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Application not found");
      setApplication(null);
    } finally {
      setLoading(false);
    }
  };

  const loadByEmail = async () => {
    if (!email.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const apps = await api.listApplications(email.trim());
      setApplications(apps);
      setApplication(apps[0] || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lookup failed");
    } finally {
      setLoading(false);
    }
  };

  const renderApp = (app: ApplicationResponse) => (
    <div className="card" key={app.application_id}>
      <h3 style={{ marginTop: 0 }}>{app.job_title || "Application"}</h3>
      <p>
        <span className={`status-pill ${app.status}`}>{app.status}</span>
      </p>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
        ID: <code>{app.application_id}</code>
        {app.created_at && <> · Submitted {new Date(app.created_at).toLocaleString()}</>}
      </p>
    </div>
  );

  return (
    <>
      <h1 className="page-title">Application Status</h1>
      <p className="page-subtitle">Look up by application ID or email.</p>

      {error && <div className="error-banner">{error}</div>}

      <div className="grid-2">
        <div className="card">
          <h3>By application ID</h3>
          <input
            value={lookupId}
            onChange={(e) => setLookupId(e.target.value)}
            placeholder="UUID from confirmation"
          />
          <button type="button" onClick={() => loadById(lookupId)} disabled={loading}>
            Look up
          </button>
        </div>
        <div className="card">
          <h3>By email</h3>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
          <button type="button" onClick={loadByEmail} disabled={loading}>
            List applications
          </button>
        </div>
      </div>

      {loading && <p style={{ color: "var(--muted)" }}>Loading…</p>}

      {applications.length > 1
        ? applications.map(renderApp)
        : application
          ? renderApp(application)
          : null}
    </>
  );
}
