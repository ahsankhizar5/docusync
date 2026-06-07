"use client";

import Link from "next/link";
import { ArrowLeft, Check, CheckCircle2, GitPullRequest, Loader2, Send, X } from "lucide-react";
import { useEffect, useState } from "react";
import { StatusPill } from "../../../components/status-pill";
import { approveJob, getJob, Job, rejectJob } from "../../../lib/api";

export default function JobDetailPage({ params }: { params: { id: string } }) {
  const [job, setJob] = useState<Job | null>(null);
  const [draft, setDraft] = useState("");
  const [reviewer, setReviewer] = useState("reviewer");
  const [comment, setComment] = useState("");
  const [busyAction, setBusyAction] = useState<"approve" | "reject" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const loaded = await getJob(params.id);
      setJob(loaded);
      setDraft(loaded.final_content || loaded.ai_patch || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load job.");
    }
  }

  async function approve() {
    if (!job || busyAction) return;
    setBusyAction("approve");
    setError(null);
    try {
      const updated = await approveJob(job.id, draft, reviewer, comment || undefined);
      setJob(updated);
      setDraft(updated.final_content || updated.ai_patch || draft);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to approve and publish.");
    } finally {
      setBusyAction(null);
    }
  }

  async function reject() {
    if (!job || busyAction) return;
    if (!comment.trim()) {
      setError("Add a short reviewer note before rejecting this draft.");
      return;
    }
    setBusyAction("reject");
    setError(null);
    try {
      const updated = await rejectJob(job.id, reviewer, comment);
      setJob(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reject draft.");
    } finally {
      setBusyAction(null);
    }
  }

  useEffect(() => {
    load();
  }, [params.id]);

  if (error && !job) {
    return <main className="content"><div className="panel">{error}</div></main>;
  }

  if (!job) {
    return <main className="content"><div className="panel">Loading job...</div></main>;
  }

  const canApprove = Boolean(draft.trim()) && !busyAction;
  const canReject = !busyAction;

  return (
    <main className="shell app-layout">
      <aside className="sidebar">
        <Link href="/" className="brand side-brand">
          <span className="brand-mark"><GitPullRequest size={20} /></span>
          <span>DocuSync</span>
        </Link>
        <nav className="side-nav">
          <Link href="/" className="side-link active"><ArrowLeft size={16} /> Review Queue</Link>
          <span className="side-label">Current Job</span>
          <span className="side-link muted-link">{job.mapped_module || "Mapping pending"}</span>
        </nav>
      </aside>

      <section className="workspace">
        <header className="workspace-topbar">
          <Link href="/" className="button subtle"><ArrowLeft size={17} /> Back</Link>
          <div className="topbar-title">
            <span className="muted">Pull Request Review</span>
            <strong>{job.repo_full_name} #{job.pr_number}</strong>
          </div>
          <StatusPill status={job.status} />
        </header>

        <div className="content workspace-content">
          {error && <div className="notice danger-notice">{error}</div>}

          <section className="review-hero review-workbench">
            <div className="hero-copy">
              <div className="eyebrow">AI documentation draft</div>
              <h1>{job.pr_title}</h1>
              <p>{job.ai_summary || "DocuSync is preparing reviewer-ready documentation from the pull request evidence."}</p>
            </div>
            <div className="review-actions">
              <input className="input" value={reviewer} onChange={(event) => setReviewer(event.target.value)} aria-label="Reviewer" />
              <input className="input" value={comment} onChange={(event) => setComment(event.target.value)} placeholder="Reviewer note or rejection reason" aria-label="Reviewer note" />
              <button className="button primary" onClick={approve} disabled={!canApprove} title="Approve and publish to Notion">
                {busyAction === "approve" ? <Loader2 size={17} className="spin" /> : <Send size={17} />}
                {busyAction === "approve" ? "Publishing" : "Approve"}
              </button>
              <button className="button danger" onClick={reject} disabled={!canReject} title="Reject draft">
                {busyAction === "reject" ? <Loader2 size={17} className="spin" /> : <X size={17} />}
                {busyAction === "reject" ? "Rejecting" : "Reject"}
              </button>
            </div>
          </section>

          <div className="meta compact-meta">
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
            <div className="meta-item breakable">
              <div className="muted">Notion target</div>
              <strong>{job.notion_target_id || "Pending"}</strong>
            </div>
          </div>

          <div className="grid">
            <section className="panel">
              <div className="panel-head compact-head">
                <div>
                  <h2>Current Documentation</h2>
                  <p className="muted">Source content from the mapped Notion page.</p>
                </div>
              </div>
              <div className="pre">{job.current_docs || "Documentation has not been retrieved yet."}</div>
            </section>
            <section className="panel">
              <div className="panel-head compact-head">
                <div>
                  <h2>Proposed Update</h2>
                  <p className="muted">Reviewer-editable Markdown before publish.</p>
                </div>
              </div>
              <textarea className="textarea" value={draft} onChange={(event) => setDraft(event.target.value)} />
            </section>
          </div>

          <div className="grid lower-grid">
            <section className="panel">
              <h3>Pull Request Evidence</h3>
              <p className="muted">{job.pr_body || "No PR description provided."}</p>
              <div className="pre">{job.diff || "Diff has not been loaded yet."}</div>
            </section>
            <section className="panel">
              <h3>Reviewer Notes</h3>
              <p>{job.reviewer_notes || "No model note was provided."}</p>
              <h3>Audit Trail</h3>
              <div className="pre compact-pre">
                {(job.audit_logs || []).map((log) => `${log.created_at} | ${log.action} | ${log.actor || ""} | ${log.comment || ""}`).join("\n")}
              </div>
            </section>
          </div>

          {job.status === "published" && (
            <div className="notice success-notice">
              <CheckCircle2 size={18} /> Published to Notion at {job.published_at}
            </div>
          )}

          {job.status === "rejected" && (
            <div className="notice danger-notice">
              <X size={18} /> Draft rejected. The audit trail keeps the reviewer reason.
            </div>
          )}

          {job.status === "published" && (
            <div className="panel inline-complete">
              <Check size={18} /> This review job is complete.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
