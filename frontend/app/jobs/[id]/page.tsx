"use client";

import Link from "next/link";
import { Check, Send, X } from "lucide-react";
import { useEffect, useState } from "react";
import { approveJob, getJob, Job, rejectJob } from "../../../lib/api";
import { StatusPill } from "../../../components/status-pill";

export default function JobDetailPage({ params }: { params: { id: string } }) {
  const [job, setJob] = useState<Job | null>(null);
  const [draft, setDraft] = useState("");
  const [reviewer, setReviewer] = useState("reviewer");
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const loaded = await getJob(params.id);
      setJob(loaded);
      setDraft(loaded.final_content || loaded.ai_patch || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load job.");
    }
  }

  async function approve() {
    if (!job) return;
    const updated = await approveJob(job.id, draft, reviewer, comment || undefined);
    setJob(updated);
  }

  async function reject() {
    if (!job || !comment.trim()) return;
    const updated = await rejectJob(job.id, reviewer, comment);
    setJob(updated);
  }

  useEffect(() => {
    load();
  }, [params.id]);

  if (error) {
    return <main className="content"><div className="panel">{error}</div></main>;
  }

  if (!job) {
    return <main className="content"><div className="panel">Loading job...</div></main>;
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <Link href="/">DocuSync Review</Link>
        </div>
        <StatusPill status={job.status} />
      </header>

      <section className="content">
        <div className="toolbar">
          <div>
            <strong>{job.pr_title}</strong>
            <div className="muted">{job.repo_full_name} #{job.pr_number}</div>
          </div>
          <div className="actions">
            <input className="input" value={reviewer} onChange={(event) => setReviewer(event.target.value)} aria-label="Reviewer" />
            <button className="button primary" onClick={approve} disabled={!draft.trim()} title="Approve and publish"><Send size={17} /> Approve</button>
            <button className="button danger" onClick={reject} disabled={!comment.trim()} title="Reject draft"><X size={17} /> Reject</button>
          </div>
        </div>

        <div className="meta">
          <div className="meta-item">
            <div className="muted">Module</div>
            <strong>{job.mapped_module || "Pending"}</strong>
          </div>
          <div className="meta-item">
            <div className="muted">Confidence</div>
            <strong>{typeof job.ai_confidence === "number" ? `${Math.round(job.ai_confidence * 100)}%` : "Pending"}</strong>
          </div>
          <div className="meta-item">
            <div className="muted">Changed files</div>
            <strong>{job.changed_files?.length || 0}</strong>
          </div>
          <div className="meta-item">
            <div className="muted">Notion target</div>
            <strong>{job.notion_target_id || "Pending"}</strong>
          </div>
        </div>

        <div className="grid">
          <section className="panel">
            <h2>Current Documentation</h2>
            <div className="pre">{job.current_docs || "Documentation has not been retrieved yet."}</div>
          </section>
          <section className="panel">
            <h2>Proposed Update</h2>
            <textarea className="textarea" value={draft} onChange={(event) => setDraft(event.target.value)} />
          </section>
        </div>

        <div className="grid" style={{ marginTop: 16 }}>
          <section className="panel">
            <h3>Pull Request Evidence</h3>
            <p className="muted">{job.pr_body || "No PR description provided."}</p>
            <div className="pre">{job.diff || "Diff has not been loaded yet."}</div>
          </section>
          <section className="panel">
            <h3>Review Notes</h3>
            <p>{job.ai_summary || "Draft is still processing."}</p>
            <p className="muted">{job.reviewer_notes}</p>
            <textarea className="textarea" style={{ minHeight: 120 }} placeholder="Approval note or rejection reason" value={comment} onChange={(event) => setComment(event.target.value)} />
            <h3 style={{ marginTop: 16 }}>Audit Trail</h3>
            <div className="pre" style={{ minHeight: 160 }}>
              {(job.audit_logs || []).map((log) => `${log.created_at} | ${log.action} | ${log.actor || ""} | ${log.comment || ""}`).join("\n")}
            </div>
          </section>
        </div>

        {job.status === "published" && (
          <div className="panel" style={{ marginTop: 16 }}>
            <Check size={18} /> Published at {job.published_at}
          </div>
        )}
      </section>
    </main>
  );
}
