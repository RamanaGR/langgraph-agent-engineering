export type Role = "recruiter" | "candidate";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export function getStoredAuth(): { role: Role; apiKey: string } {
  const role = (localStorage.getItem("ts_role") as Role) || "recruiter";
  const apiKey =
    localStorage.getItem("ts_api_key") ||
    (role === "recruiter" ? "recruiter-dev-key" : "candidate-dev-key");
  return { role, apiKey };
}

export function setStoredAuth(role: Role, apiKey: string) {
  localStorage.setItem("ts_role", role);
  localStorage.setItem("ts_api_key", apiKey);
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  role?: Role,
): Promise<T> {
  const auth = getStoredAuth();
  const activeRole = role || auth.role;
  const headers = new Headers(options.headers);
  headers.set("X-API-Key", auth.apiKey);
  headers.set("X-Role", activeRole);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    const message =
      typeof detail.detail === "string"
        ? detail.detail
        : detail.detail?.message || JSON.stringify(detail.detail || detail);
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export interface QueryHit {
  chunk_id: string;
  document_id: string;
  doc_type: string;
  filename: string | null;
  text: string | null;
  score: number;
}

export interface QueryResponse {
  query: string;
  sanitized_query: string;
  rewritten_queries: string[];
  hits: QueryHit[];
  answer?: {
    answer: string;
    citations: { chunk_id: string; quote: string }[];
    confidence: number;
  };
  retrieval_mode: string;
  cache_hit: boolean;
}

export interface RankedCandidate {
  name: string;
  years_experience?: number | null;
  skills?: string[];
  fit_score: number;
  matched_skills?: string[];
  gaps?: string[];
  interview_questions?: string[];
}

export interface CandidateFitResult {
  ranked_candidates?: RankedCandidate[];
  top_candidate?: RankedCandidate | null;
  query_skills?: string[];
  min_years?: number | null;
  no_strong_matches?: boolean;
  no_match_reason?: string | null;
  required_skills?: string[];
}

export interface AgentTaskResults {
  candidate_fit?: CandidateFitResult;
  [key: string]: unknown;
}

export interface AgentChatResponse {
  thread_id: string;
  response: string | null;
  intent: string | null;
  rewritten_queries: string[] | null;
  task_results: AgentTaskResults | null;
  interrupted: boolean;
  requires_hitl: boolean;
  pending_approval: Record<string, unknown> | null;
}

export interface PendingApproval {
  thread_id: string;
  tenant_id: string;
  pending_approval: Record<string, unknown>;
  preview: string | null;
  created_at: string | null;
}

export interface JobSummary {
  job_id: string;
  title: string;
  location: string | null;
  required_skills: string[];
  description?: string | null;
}

export interface ApplicationResponse {
  application_id: string;
  job_id: string;
  job_title: string | null;
  full_name: string;
  email: string;
  status: string;
  created_at: string | null;
}

export const api = {
  query: (query: string, retrievalMode = "hybrid") =>
    request<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify({ query, retrieval_mode: retrievalMode, generate_answer: true }),
    }),

  agentChat: (message: string, threadId?: string) =>
    request<AgentChatResponse>("/agents/chat", {
      method: "POST",
      body: JSON.stringify({ message, thread_id: threadId }),
    }),

  resumeAgent: (threadId: string, action: "approve" | "reject") =>
    request<{ thread_id: string; status: string; response: string | null }>(
      `/agents/resume/${threadId}`,
      { method: "POST", body: JSON.stringify({ action }) },
    ),

  listPending: () => request<PendingApproval[]>("/agents/pending"),

  ingest: (file: File, docType: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("doc_type", docType);
    return request<{ document_id: string; status: string; idempotent_skip: boolean }>(
      "/ingest",
      { method: "POST", body: form },
    );
  },

  listJobs: () => request<JobSummary[]>("/jobs"),

  getJob: (jobId: string) => request<JobSummary>(`/jobs/${jobId}`),

  apply: (jobId: string, fullName: string, email: string, notes: string, resume?: File) => {
    const form = new FormData();
    form.append("job_id", jobId);
    form.append("full_name", fullName);
    form.append("email", email);
    form.append("notes", notes);
    if (resume) form.append("resume", resume);
    return request<{ application_id: string; status: string }>("/applications", {
      method: "POST",
      body: form,
    }, "candidate");
  },

  getApplication: (id: string) => request<ApplicationResponse>(`/applications/${id}`),

  listApplications: (email?: string) =>
    request<ApplicationResponse[]>(
      email ? `/applications?email=${encodeURIComponent(email)}` : "/applications",
    ),
};
