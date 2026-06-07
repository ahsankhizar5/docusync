"use client";

import Link from "next/link";
import { CheckCircle2, CircleAlert, FilePlus2, RefreshCw, Trash2, Workflow } from "lucide-react";
import { useEffect, useState } from "react";
import { StatusPill } from "../components/status-pill";
import { clearFailedJobs, createDemoJob, getSetupStatus, Job, listJobs, SetupStatus } from "../lib/api";

export default function HomePage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFailed, setShowFailed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(includeFailed = showFailed) {
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
    }
  }

  async function seedDemo() {
    await createDemoJob();
    setTimeout(() => load(showFailed), 700);
  }

  async function clearFailures() {
    setError(null);
    await clearFailedJobs();
    setShowFailed(false);
    await load(false);
  }

  useEffect(() => {
    load(false);
  }, []);

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark"><Workflow size={20} /></span>
          <span>DocuSync Review</span>
        </div>
        <span className="muted">GitHub PRs to reviewed Notion documentation</span>
      </header>

      <section className="content">
        <div className="toolbar">
          <div>
            <strong>Review Queue</strong>
            <div className="muted">Approve, edit, or reject AI-generated documentation updates from merged GitHub pull requests.</div>
          </div>
          <div className="actions">
            <button className="button" onClick={() => load(showFailed)} title="Refresh jobs"><RefreshCw size={17} /> Refresh</button>
            <button className="button danger" onClick={clearFailures} title="Remove failed history"><Trash2 size={17} /> Clear failed</button>
            <button
              className="button"
              onClick={() => {
                const next = !showFailed;
                setShowFailed(next);
                load(next);
              }}
              title="Toggle failed jobs"
            >
              {showFailed ? "Hide failed" : "Show failed"}
            </button>
            <button className="button" onClick={seedDemo} title="Development-only test job"><FilePlus2 size={17} /> Dev test job</button>
          </div>
        </div>

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

        {error && <div className="panel">{error}</div>}
        {loading && <div className="panel">Loading jobs...</div>}
        {!loading && jobs.length === 0 && <div className="panel">No review jobs yet. In production, merged GitHub pull requests will appear here automatically.</div>}

        {!loading && jobs.length > 0 && (
          <div className="panel jobs">
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
    </main>
  );
}
