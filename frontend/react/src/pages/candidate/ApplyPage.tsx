import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api/client";

export function ApplyPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [jobTitle, setJobTitle] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [notes, setNotes] = useState("");
  const [resume, setResume] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applicationId, setApplicationId] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    api
      .getJob(jobId)
      .then((job) => setJobTitle(job.title))
      .catch(() => setJobTitle("Position"));
  }, [jobId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.apply(jobId, fullName, email, notes, resume || undefined);
      setApplicationId(res.application_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Application failed");
    } finally {
      setLoading(false);
    }
  };

  if (applicationId) {
    return (
      <>
        <h1 className="page-title">Application Submitted</h1>
        <div className="success-banner">
          Your application <strong>{applicationId}</strong> has been received.
        </div>
        <Link to={`/candidate/status?id=${applicationId}`}>
          <button type="button">Track status</button>
        </Link>
      </>
    );
  }

  return (
    <>
      <h1 className="page-title">Apply — {jobTitle}</h1>
      <p className="page-subtitle">Submit your details and optional resume.</p>

      {error && <div className="error-banner">{error}</div>}

      <form className="card" onSubmit={handleSubmit}>
        <label>Full name</label>
        <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />

        <label>Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label>Cover note (optional)</label>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />

        <label>Resume (PDF, DOCX, or TXT)</label>
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(e) => setResume(e.target.files?.[0] || null)}
        />

        <button type="submit" disabled={loading}>
          {loading ? "Submitting…" : "Submit application"}
        </button>
      </form>
    </>
  );
}
