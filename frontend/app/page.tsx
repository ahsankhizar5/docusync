"use client";

import Link from "next/link";
import { CheckCircle2, CircleAlert, FilePlus2, GitPullRequest, Loader2, RefreshCw, Trash2, Workflow } from "lucide-react";
import { useEffect, useState } from "react";
import { StatusPill } from "../components/status-pill";
import { clearFailedJobs, createDemoJob, getSetupStatus, Job, listJobs, SetupStatus } from "../lib/api";

type QueueAction = "refresh" | "demo" | "clear" | "toggle" | null;

export default function HomePage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFailed, setShowFailed] = useState(false);
  const [busyAction, setBusyAction] = useState<QueueAction>(null);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    load(false, null);
  }, []);

  const pendingCount = jobs.filter((job) => job.status === "awaiting_review").length;
  const publishedCount = jobs.filter((job) => job.status === "published").length;

  return (
    <main className="shell app-layout">
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
            <span className="muted">Documentation automation</span>
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

        <section className="content workspace-content">
          <section className="review-hero queue-hero">
            <div>
              <div className="eyebrow">Production review command center</div>
              <h1>Review Queue</h1>
              <p>Approve, edit, or reject AI-generated Notion documentation updates from merged GitHub pull requests.</p>
            </div>
            <div className="queue-stats">
              <div><span>{jobs.length}</span><strong>Visible jobs</strong></div>
              <div><span>{pendingCount}</span><strong>Awaiting review</strong></div>
              <div><span>{publishedCount}</span><strong>Published</strong></div>
            </div>
          </section>

          {setup && (
            <section className="panel setup-panel">
              <div>
                <strong>Production Setup</strong>
                <div className="muted">
                  Frontend: {setup.deployment.frontend} | Backend: {setup.deployment.backend} | Repo: {setup.deployment.github_repo}
                </div>
                <div className="muted setup-note">
                  Live trigger: open a pull request, merge it, and GitHub will send the merged PR event. Creating a branch alone will not create a review job.
                </div>
              </div>
              <div className="setup-grid">
                {setup.checks.map((check) => (
                  <div className="setup-item" key={check.id}>
                    {check.configured ? <CheckCircle2 size={18} className="ok-icon" /> : <CircleAlert size={18} className="warn-icon" />}
                    <div>
                      <strong>{check.label}</strong>
                      <div className="muted">{check.detail}</div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="panel queue-panel">
            <div className="panel-head">
              <div>
                <h2>Incoming Documentation Jobs</h2>
                <p className="muted">{showFailed ? "Showing active and failed jobs." : "Failed jobs are hidden to keep the production queue clean."}</p>
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
                {jobs.map((job) => (
                  <Link href={`/jobs/${job.id}`} className="job-row" key={job.id}>
                    <div>
                      <strong>{job.pr_title}</strong>
                      <div className="muted">{job.repo_full_name} #{job.pr_number}</div>
                    </div>
                    <StatusPill status={job.status} />
                    <span className="muted">{job.mapped_module || "Mapping pending"}</span>
                    <span className="muted">{new Date(job.created_at).toLocaleDateString()}</span>
                  </Link>
                ))}
              </div>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}
