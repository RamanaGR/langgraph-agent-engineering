import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type JobSummary } from "../../api/client";

export function JobsPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listJobs()
      .then(setJobs)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load jobs"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <h1 className="page-title">Open Positions</h1>
      <p className="page-subtitle">Browse roles and submit your application.</p>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p style={{ color: "var(--muted)" }}>Loading jobs…</p>}

      {jobs.map((job) => (
        <div key={job.job_id} className="card">
          <h3 style={{ marginTop: 0 }}>{job.title}</h3>
          {job.location && (
            <p style={{ color: "var(--muted)", margin: "0 0 0.5rem" }}>{job.location}</p>
          )}
          {job.description && <p>{job.description}</p>}
          <div className="skill-tags" style={{ marginBottom: "1rem" }}>
            {job.required_skills.map((skill) => (
              <span key={skill} className="skill-tag">
                {skill}
              </span>
            ))}
          </div>
          <Link to={`/candidate/apply/${job.job_id}`}>
            <button type="button">Apply</button>
          </Link>
        </div>
      ))}
    </>
  );
}
