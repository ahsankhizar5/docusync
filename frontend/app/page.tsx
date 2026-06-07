"use client";

import Link from "next/link";
import { CheckCircle2, CircleAlert, FilePlus2, RefreshCw, Workflow } from "lucide-react";
import { useEffect, useState } from "react";
import { createDemoJob, getSetupStatus, Job, listJobs, SetupStatus } from "../lib/api";
import { StatusPill } from "../components/status-pill";

export default function HomePage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [loadedSetup, loadedJobs] = await Promise.all([getSetupStatus(), listJobs()]);
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
    setTimeout(load, 700);
  }

  useEffect(() => {
    load();
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
            <div className="muted">Approve, edit, or reject AI-generated documentation updates.</div>
          </div>
          <div className="actions">
            <button className="button" onClick={load} title="Refresh jobs"><RefreshCw size={17} /> Refresh</button>
            <button className="button" onClick={seedDemo} title="Development-only test job"><FilePlus2 size={17} /> Dev test job</button>
          </div>
        </div>

        {setup && (
          <section className="panel setup-panel">
            <div>
              <strong>Production Setup</strong>
              <div className="muted">
                Frontend: {setup.deployment.frontend} · Backend: {setup.deployment.backend} · Repo: {setup.deployment.github_repo}
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
