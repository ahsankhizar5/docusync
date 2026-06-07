from uuid import uuid4

from ..models import DemoJobRequest
from .github import PullRequestEvent


DEMO_SCENARIOS = [
    {
        "title": "Add password reset expiry policy",
        "body": "Implements 15-minute reset token expiry and invalidates used tokens.",
        "changed_files": ["backend/app/services/auth.py"],
        "diff": """diff --git a/backend/app/services/auth.py b/backend/app/services/auth.py
@@
- token = create_reset_token(user)
+ token = create_reset_token(user, expires_in_minutes=15)
+ mark_reset_token_used(token)
""",
    },
    {
        "title": "Introduce webhook retry audit trail",
        "body": "Stores retry attempts and terminal webhook delivery errors for operations review.",
        "changed_files": ["backend/app/services/jobs.py"],
        "diff": """diff --git a/backend/app/services/jobs.py b/backend/app/services/jobs.py
@@
+ conn.execute(insert(audit_logs).values(job_id=job_id, action="retry_scheduled", actor="docusync"))
+ retry_count = min(job.retry_count + 1, settings.max_retry_attempts)
""",
    },
    {
        "title": "Improve review queue filtering controls",
        "body": "Adds status filters so reviewers can separate active, published, rejected, and failed jobs.",
        "changed_files": ["frontend/app/page.tsx"],
        "diff": """diff --git a/frontend/app/page.tsx b/frontend/app/page.tsx
@@
+ const filteredJobs = jobs.filter((job) => selectedStatus === "all" || job.status === selectedStatus)
+ <StatusFilter value={selectedStatus} onChange={setSelectedStatus} />
""",
    },
    {
        "title": "Document production webhook setup",
        "body": "Updates project documentation with the exact GitHub webhook payload URL and merge-event trigger.",
        "changed_files": ["docs/deployment.md"],
        "diff": """diff --git a/docs/deployment.md b/docs/deployment.md
@@
+ GitHub webhook payload URL: /_backend/webhooks/github
+ Subscribe to pull_request events and process only closed events where merged is true.
""",
    },
    {
        "title": "Add Notion publish failure handling",
        "body": "Captures Notion API publish failures and keeps approved drafts available for retry.",
        "changed_files": ["backend/app/services/notion.py"],
        "diff": """diff --git a/backend/app/services/notion.py b/backend/app/services/notion.py
@@
+ if response.status_code >= 500:
+     raise NotionPublishRetryableError("Notion publish failed; retry later.")
""",
    },
]


def build_demo_event(request: DemoJobRequest) -> PullRequestEvent:
    run_id = uuid4().hex[:8]
    scenario = DEMO_SCENARIOS[int(run_id[:4], 16) % len(DEMO_SCENARIOS)]
    title = request.pr_title or f"{scenario['title']} [{run_id}]"
    changed_files = request.changed_files or list(scenario["changed_files"])

    return PullRequestEvent(
        repo_full_name=request.repo_full_name or "demo/docusync-target",
        pr_number=request.pr_number or int(run_id[:6], 16),
        pr_title=title,
        pr_body=request.pr_body or scenario["body"],
        pr_url=None,
        merged_by="demo-user",
        changed_files=changed_files,
        diff=request.diff or scenario["diff"],
    )
