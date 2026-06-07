"use client";

import { Check, ChevronDown, Code2, FileText, FilePlus2, GitPullRequest, History, Loader2, RefreshCw, Send, Sparkles, Trash2, Workflow, X } from "lucide-react";
import { useEffect, useState } from "react";
import { SystemIntegrity, SystemIntegritySkeleton } from "../components/system-integrity";
import { StatusPill } from "../components/status-pill";
import { approveJob, clearFailedJobs, createDemoJob, getJob, getSetupStatus, Job, listJobs, rejectJob, SetupStatus } from "../lib/api";

type QueueAction = "refresh" | "demo" | "clear" | "toggle" | null;
type ReviewAction = "approve" | "reject" | null;

export default function HomePage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFailed, setShowFailed] = useState(false);
  const [busyAction, setBusyAction] = useState<QueueAction>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedJobId, setExpandedJobId] = useState<number | null>(null);
  const [expandedJob, setExpandedJob] = useState<Job | null>(null);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerError, setDrawerError] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [reviewer, setReviewer] = useState("reviewer");
  const [reviewComment, setReviewComment] = useState("");
  const [reviewAction, setReviewAction] = useState<ReviewAction>(null);

  async function load(includeFailed = showFailed, action: QueueAction = "refresh") {
    setBusyAction(action);
    setLoading(true);
    setError(null);
    try {
      const [loadedSetup, loadedJobs] = await Promise.all([getSetupStatus(), listJobs(includeFailed)]);
      setSetup(loadedSetup);
      setJobs(loadedJobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load jobs.");
    } finally {
      setLoading(false);
      setBusyAction(null);
    }
  }

  async function seedDemo() {
    setBusyAction("demo");
    setError(null);
    try {
      await createDemoJob();
      await new Promise((resolve) => setTimeout(resolve, 500));
      await load(showFailed, "demo");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create demo job.");
      setBusyAction(null);
    }
  }

  async function clearFailures() {
    setBusyAction("clear");
    setError(null);
    try {
      await clearFailedJobs();
      setShowFailed(false);
      await load(false, "clear");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to clear failed jobs.");
      setBusyAction(null);
    }
  }

  function toggleFailed() {
    const next = !showFailed;
    setShowFailed(next);
    load(next, "toggle");
  }

  async function toggleJobDrawer(job: Job) {
    if (expandedJobId === job.id) {
      setExpandedJobId(null);
      setExpandedJob(null);
      setDrawerError(null);
      return;
    }

    setExpandedJobId(job.id);
    setExpandedJob(null);
    setDrawerError(null);
    setDrawerLoading(true);
    try {
      const loaded = await getJob(String(job.id));
      setExpandedJob(loaded);
      setDraft(loaded.final_content || loaded.ai_patch || "");
      setReviewComment("");
    } catch (err) {
      setDrawerError(err instanceof Error ? err.message : "Unable to load job details.");
    } finally {
      setDrawerLoading(false);
    }
  }

  function replaceJob(updated: Job) {
    setJobs((current) => current.map((job) => (job.id === updated.id ? { ...job, ...updated } : job)));
    setExpandedJob(updated);
    setDraft(updated.final_content || updated.ai_patch || draft);
  }

  async function approveExpandedJob() {
    if (!expandedJob || !draft.trim() || reviewAction) return;
    setReviewAction("approve");
    setDrawerError(null);
    try {
      const updated = await approveJob(expandedJob.id, draft, reviewer, reviewComment || undefined);
      replaceJob(updated);
    } catch (err) {
      setDrawerError(err instanceof Error ? err.message : "Unable to approve and publish this job.");
    } finally {
      setReviewAction(null);
    }
  }

  async function rejectExpandedJob() {
    if (!expandedJob || reviewAction) return;
    if (!reviewComment.trim()) {
      setDrawerError("Add a reviewer note before rejecting this draft.");
      return;
    }
    setReviewAction("reject");
    setDrawerError(null);
    try {
      const updated = await rejectJob(expandedJob.id, reviewer, reviewComment);
      replaceJob(updated);
    } catch (err) {
      setDrawerError(err instanceof Error ? err.message : "Unable to reject this job.");
    } finally {
      setReviewAction(null);
    }
  }

  useEffect(() => {
    load(false, null);
  }, []);

  const pendingCount = jobs.filter((job) => job.status === "awaiting_review").length;
  const publishedCount = jobs.filter((job) => job.status === "published").length;

  return (
    <main className="shell app-layout premium-shell">
      <aside className="sidebar">
        <div className="brand side-brand">
          <span className="brand-mark"><Workflow size={20} /></span>
          <span>DocuSync</span>
        </div>
        <nav className="side-nav">
          <span className="side-link active"><GitPullRequest size={16} /> Review Queue</span>
          <span className="side-label">Operations</span>
          <span className="side-link muted-link">GitHub Webhooks</span>
          <span className="side-link muted-link">Notion Publishing</span>
          <span className="side-link muted-link">Audit Logs</span>
        </nav>
      </aside>

      <section className="workspace">
        <header className="workspace-topbar">
          <div className="topbar-title">
            <span className="muted">Enterprise documentation control plane</span>
            <strong>DocuSync Review</strong>
          </div>
          <div className="topbar-actions">
            <button className="button" onClick={() => load(showFailed, "refresh")} disabled={Boolean(busyAction)} title="Refresh jobs">
              {busyAction === "refresh" ? <Loader2 size={17} className="spin" /> : <RefreshCw size={17} />}
              Refresh
            </button>
            <button className="button primary" onClick={seedDemo} disabled={Boolean(busyAction)} title="Development-only test job">
              {busyAction === "demo" ? <Loader2 size={17} className="spin" /> : <FilePlus2 size={17} />}
              Dev test job
            </button>
          </div>
        </header>

        <section className="content workspace-content dashboard-bento">
          <section className="glass-card review-hero queue-hero bento-hero">
            <div className="hero-copy">
              <div className="eyebrow"><Sparkles size={13} /> Production review command center</div>
              <h1>Review Queue</h1>
              <p>Merged pull requests become controlled Notion documentation updates with review, audit, and publish gates.</p>
            </div>
            <div className="queue-stats">
              <div><span>{jobs.length}</span><strong>Visible</strong></div>
              <div><span>{pendingCount}</span><strong>Review</strong></div>
              <div><span>{publishedCount}</span><strong>Published</strong></div>
            </div>
          </section>

          {setup ? <SystemIntegrity setup={setup} /> : <SystemIntegritySkeleton />}

          <section className="glass-card queue-panel bento-queue">
            <div className="panel-head">
              <div>
                <h2>Incoming Documentation Jobs</h2>
                <p className="muted">{showFailed ? "Active and failed jobs are visible." : "Failed jobs are hidden from the operating queue."}</p>
              </div>
              <div className="actions">
                <button className="button danger" onClick={clearFailures} disabled={Boolean(busyAction)} title="Remove failed history">
                  {busyAction === "clear" ? <Loader2 size={17} className="spin" /> : <Trash2 size={17} />}
                  Clear failed
                </button>
                <button className="button" onClick={toggleFailed} disabled={Boolean(busyAction)} title="Toggle failed jobs">
                  {busyAction === "toggle" ? <Loader2 size={17} className="spin" /> : null}
                  {showFailed ? "Hide failed" : "Show failed"}
                </button>
              </div>
            </div>

            {error && <div className="notice danger-notice">{error}</div>}
            {loading && <div className="empty-state">Loading jobs...</div>}
            {!loading && jobs.length === 0 && <div className="empty-state">No review jobs yet. Merged GitHub pull requests will appear here automatically.</div>}

            {!loading && jobs.length > 0 && (
              <div className="jobs">
                <div className="job-row job-head">
                  <span>Pull request</span>
                  <span>Status</span>
                  <span>Module</span>
                  <span>Created</span>
                </div>
                {jobs.map((job) => (
                  <div className="job-stream-item" key={job.id}>
                    <button
                      className={`job-row job-trigger ${expandedJobId === job.id ? "expanded" : ""}`}
                      onClick={() => toggleJobDrawer(job)}
                      type="button"
                    >
                      <div className="job-title">
                        <strong>{job.pr_title}</strong>
                        <div className="muted">{job.repo_full_name} #{job.pr_number}</div>
                      </div>
                      <StatusPill status={job.status} />
                      <span className="muted">{job.mapped_module || "Mapping pending"}</span>
                      <span className="muted job-date">
                        {new Date(job.created_at).toLocaleDateString()}
                        <ChevronDown size={16} />
                      </span>
                    </button>

                    {expandedJobId === job.id && (
                      <div className="job-drawer">
                        {drawerLoading && (
                          <div className="drawer-loading">
                            <Loader2 size={18} className="spin" />
                            Loading Gemini analysis and pull request evidence...
                          </div>
                        )}

                        {drawerError && (
                          <div className="notice danger-notice">{drawerError}</div>
                        )}

                        {expandedJob && (
                          <>
                            <div className="drawer-head">
                              <div>
                                <div className="eyebrow"><Sparkles size={13} /> Gemini patch brief</div>
                                <h3>{expandedJob.ai_summary || "Draft is still processing."}</h3>
                                <p>{expandedJob.reviewer_notes || "No reviewer note has been generated yet."}</p>
                              </div>
                              <div className="drawer-status">
                                <StatusPill status={expandedJob.status} />
                                <button className="button subtle drawer-close" onClick={() => toggleJobDrawer(job)} type="button" title="Close drawer">
                                  <X size={16} />
                                </button>
                              </div>
                            </div>

                            <div className="review-console">
                              <input className="input reviewer-input" value={reviewer} onChange={(event) => setReviewer(event.target.value)} aria-label="Reviewer" />
                              <input
                                className="input review-note-input"
                                value={reviewComment}
                                onChange={(event) => setReviewComment(event.target.value)}
                                placeholder="Reviewer note or rejection reason"
                                aria-label="Reviewer note"
                              />
                              <button className="button primary" onClick={approveExpandedJob} disabled={!draft.trim() || Boolean(reviewAction)} type="button">
                                {reviewAction === "approve" ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
                                {reviewAction === "approve" ? "Publishing" : "Approve"}
                              </button>
                              <button className="button danger" onClick={rejectExpandedJob} disabled={Boolean(reviewAction)} type="button">
                                {reviewAction === "reject" ? <Loader2 size={16} className="spin" /> : <X size={16} />}
                                {reviewAction === "reject" ? "Rejecting" : "Reject"}
                              </button>
                            </div>

                            <div className="drawer-grid">
                              <section className="drawer-panel drawer-panel-edit">
                                <div className="drawer-panel-title"><FileText size={15} /> Proposed Markdown Patch</div>
                                <textarea value={draft} onChange={(event) => setDraft(event.target.value)} />
                              </section>
                              <section className="drawer-panel">
                                <div className="drawer-panel-title"><Code2 size={15} /> Git Diff Evidence</div>
                                <pre>{expandedJob.diff || "Diff is not available for this job."}</pre>
                              </section>
                            </div>

                            <div className="drawer-meta-grid">
                              <section className="drawer-panel">
                                <div className="drawer-panel-title"><Check size={15} /> Current Documentation</div>
                                <pre>{expandedJob.current_docs || "Current Notion documentation has not been retrieved yet."}</pre>
                              </section>
                              <section className="drawer-panel">
                                <div className="drawer-panel-title"><History size={15} /> Audit Trail</div>
                                <pre>
                                  {(expandedJob.audit_logs || [])
                                    .map((log) => `${new Date(log.created_at).toLocaleString()} | ${log.action} | ${log.actor || ""} | ${log.comment || ""}`)
                                    .join("\n") || "No audit entries yet."}
                                </pre>
                              </section>
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}
