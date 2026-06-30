import { useState } from "react";
import { api } from "../../api/client";

const DOC_TYPES = [
  { value: "resume", label: "Resume" },
  { value: "job_description", label: "Job Description" },
  { value: "interview_notes", label: "Interview Notes" },
  { value: "other", label: "Other" },
];

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState("resume");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.ingest(file, docType);
      setResult(
        res.idempotent_skip
          ? `Skipped (duplicate): document ${res.document_id}`
          : `Queued: document ${res.document_id} — status ${res.status}`,
      );
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1 className="page-title">Document Upload</h1>
      <p className="page-subtitle">
        Upload resumes, job descriptions, or interview notes for ingestion and RAG indexing.
      </p>

      {error && <div className="error-banner">{error}</div>}
      {result && <div className="success-banner">{result}</div>}

      <div className="card">
        <label>Document type</label>
        <select value={docType} onChange={(e) => setDocType(e.target.value)}>
          {DOC_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>

        <label>File</label>
        <input
          type="file"
          accept=".pdf,.docx,.txt,.md"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />

        <button onClick={handleUpload} disabled={!file || loading}>
          {loading ? "Uploading…" : "Upload & Ingest"}
        </button>
      </div>
    </>
  );
}
