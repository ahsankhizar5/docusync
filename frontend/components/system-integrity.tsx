import { Activity, CheckCircle2, CircleAlert, Server } from "lucide-react";
import { SetupStatus } from "../lib/api";

type SystemIntegrityProps = {
  setup: SetupStatus;
};

export function SystemIntegrity({ setup }: SystemIntegrityProps) {
  const readyCount = setup.checks.filter((check) => check.configured).length;
  const totalCount = setup.checks.length;
  const integrity = totalCount === 0 ? 0 : Math.round((readyCount / totalCount) * 100);

  return (
    <section className="glass-card integrity-card">
      <div className="integrity-header">
        <div>
          <div className="eyebrow">System Integrity</div>
          <h2>{integrity}% operational</h2>
          <p>Live configuration state across LLM, Notion, GitHub, and module routing.</p>
        </div>
        <div className="integrity-orb" aria-label={`${readyCount} of ${totalCount} checks configured`}>
          <Activity size={22} />
          <span>{readyCount}/{totalCount}</span>
        </div>
      </div>

      <div className="integrity-strip">
        <div>
          <span>Frontend</span>
          <strong>{setup.deployment.frontend}</strong>
        </div>
        <div>
          <span>Backend</span>
          <strong>{setup.deployment.backend}</strong>
        </div>
        <div>
          <span>Repository</span>
          <strong>{setup.deployment.github_repo}</strong>
        </div>
      </div>

      <div className="integrity-checks">
        {setup.checks.map((check) => (
          <div className="integrity-check" data-state={check.configured ? "ready" : "warn"} key={check.id}>
            <span className="ambient-dot">
              {check.configured ? <CheckCircle2 size={15} /> : <CircleAlert size={15} />}
            </span>
            <div>
              <strong>{check.label}</strong>
              <span>{check.detail}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="integrity-footer">
        <Server size={14} />
        <span>Production jobs are triggered after GitHub pull requests are merged.</span>
      </div>
    </section>
  );
}

export function SystemIntegritySkeleton() {
  return (
    <section className="glass-card integrity-card integrity-skeleton">
      <div className="integrity-header">
        <div>
          <div className="eyebrow">System Integrity</div>
          <h2>Syncing status</h2>
          <p>DocuSync is checking backend configuration, integrations, and module routing.</p>
        </div>
        <div className="integrity-orb skeleton-orb">
          <Activity size={22} />
          <span>...</span>
        </div>
      </div>
      <div className="skeleton-lines">
        <span />
        <span />
        <span />
      </div>
    </section>
  );
}
