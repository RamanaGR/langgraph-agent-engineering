import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout({ mode }: { mode: "recruiter" | "candidate" }) {
  const { role, apiKey, setAuth } = useAuth();

  const recruiterLinks = (
    <>
      <NavLink to="/recruiter/upload">Upload</NavLink>
      <NavLink to="/recruiter/search">Search & Chat</NavLink>
      <NavLink to="/recruiter/approvals">Approvals</NavLink>
    </>
  );

  const candidateLinks = (
    <>
      <NavLink to="/candidate/jobs">Jobs</NavLink>
      <NavLink to="/candidate/status">My Applications</NavLink>
    </>
  );

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to={mode === "recruiter" ? "/recruiter" : "/candidate"} className="brand">
          Talent<span>Screen</span>
        </Link>
        <nav className="nav-links">
          {mode === "recruiter" ? recruiterLinks : candidateLinks}
          <Link to={mode === "recruiter" ? "/candidate" : "/recruiter"}>
            Switch to {mode === "recruiter" ? "Candidate" : "Recruiter"}
          </Link>
          <span className="role-badge">{role}</span>
        </nav>
      </header>
      <main className="main-content">
        <details className="card" style={{ marginBottom: "1rem" }}>
          <summary style={{ cursor: "pointer", color: "var(--muted)" }}>API settings</summary>
          <div className="settings-panel" style={{ marginTop: "0.75rem" }}>
            <div>
              <label>Role</label>
              <select
                value={role}
                onChange={(e) => setAuth(e.target.value as "recruiter" | "candidate", apiKey)}
              >
                <option value="recruiter">Recruiter</option>
                <option value="candidate">Candidate</option>
              </select>
            </div>
            <div>
              <label>API Key</label>
              <input
                value={apiKey}
                onChange={(e) => setAuth(role, e.target.value)}
                placeholder="recruiter-dev-key"
              />
            </div>
          </div>
        </details>
        <Outlet />
      </main>
    </div>
  );
}
