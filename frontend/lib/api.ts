export type AuditLog = {
  id: number;
  job_id: number;
  action: string;
  actor?: string;
  comment?: string;
  created_at: string;
};

export type Job = {
  id: number;
  status: string;
  repo_full_name: string;
  pr_number: number;
  pr_title: string;
  pr_url?: string;
  pr_body?: string;
  merged_by?: string;
  changed_files?: string[];
  diff?: string;
  mapped_module?: string;
  notion_target_id?: string;
  current_docs?: string;
  ai_summary?: string;
  ai_patch?: string;
  ai_confidence?: number;
  reviewer_notes?: string;
  final_content?: string;
  error?: string;
  created_at: string;
  updated_at: string;
  published_at?: string;
  audit_logs?: AuditLog[];
};

export type SetupCheck = {
  id: string;
  label: string;
  configured: boolean;
  detail: string;
};

export type SetupStatus = {
  environment: string;
  checks: SetupCheck[];
  deployment: {
    frontend: string;
    backend: string;
    github_repo: string;
  };
};

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "/_backend").trim().split(/\s+/)[0].replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {})
      },
      cache: "no-store"
    });
  } catch (error) {
    throw new Error(`Unable to reach DocuSync API at ${url}. Check NEXT_PUBLIC_API_BASE_URL and backend deployment.`);
  }

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request to ${url} failed with ${response.status}`);
  }
  return response.json();
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      cache: "no-store"
    });
    return response.ok;
  } catch {
    return false;
  }
}

export function listJobs(includeFailed = false): Promise<Job[]> {
  return request<Job[]>(`/api/jobs?include_failed=${includeFailed ? "true" : "false"}&limit=50`);
}

export function getSetupStatus(): Promise<SetupStatus> {
  return request<SetupStatus>("/api/setup/status");
}

export function getJob(id: string): Promise<Job> {
  return request<Job>(`/api/jobs/${id}`);
}

export function createDemoJob(): Promise<{ accepted: boolean; job_id: number }> {
  return request("/api/demo/jobs", { method: "POST", body: JSON.stringify({}) });
}

export function clearFailedJobs(): Promise<{ deleted: number }> {
  return request("/api/jobs/failed", { method: "DELETE" });
}

export function approveJob(id: number, finalContent: string, reviewer: string, comment?: string): Promise<Job> {
  return request<Job>(`/api/jobs/${id}/approve`, {
    method: "POST",
    body: JSON.stringify({ final_content: finalContent, reviewer, comment })
  });
}

export function rejectJob(id: number, reviewer: string, comment: string): Promise<Job> {
  return request<Job>(`/api/jobs/${id}/reject`, {
    method: "POST",
    body: JSON.stringify({ reviewer, comment })
  });
}
