import json
from datetime import datetime, timezone

from ..database import connect, row_to_dict
from ..settings import get_settings
from .github import PullRequestEvent
from .llm import LLMClient
from .mapping import load_mappings, select_mapping
from .notion import NotionClient


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(event: PullRequestEvent) -> int:
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO jobs (
                status, repo_full_name, pr_number, pr_title, pr_url, pr_body, merged_by,
                changed_files, diff, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "queued",
                event.repo_full_name,
                event.pr_number,
                event.pr_title,
                event.pr_url,
                event.pr_body,
                event.merged_by,
                json.dumps(event.changed_files),
                event.diff,
                now_iso(),
            ),
        )
        job_id = int(cursor.lastrowid)
        conn.execute("INSERT INTO audit_logs (job_id, action, actor, comment) VALUES (?, ?, ?, ?)", (job_id, "queued", "github", "Webhook event accepted."))
        return job_id


async def process_job(job_id: int) -> None:
    settings = get_settings()
    try:
        job = get_job(job_id)
        if not job:
            return
        mappings = load_mappings(settings.module_mapping_file)
        changed_files = job["changed_files"]
        if isinstance(changed_files, str):
            changed_files = json.loads(changed_files)
        mapping = select_mapping(changed_files, mappings)
        if mapping is None:
            raise ValueError("No module mapping configured.")
        notion = NotionClient(settings)
        current_docs = await notion.retrieve_markdown(mapping.notion_target_id, mapping.fallback_docs)
        draft = await LLMClient(settings).generate(current_docs, job["pr_title"], job["pr_body"] or "", job["diff"])
        with connect() as conn:
            conn.execute(
                """
                UPDATE jobs SET status=?, mapped_module=?, notion_target_id=?, current_docs=?,
                    ai_summary=?, ai_patch=?, ai_confidence=?, reviewer_notes=?, updated_at=?
                WHERE id=?
                """,
                (
                    "awaiting_review",
                    mapping.module,
                    mapping.notion_target_id,
                    current_docs,
                    draft.summary,
                    draft.patch,
                    draft.confidence,
                    draft.reviewer_notes,
                    now_iso(),
                    job_id,
                ),
            )
            conn.execute("INSERT INTO audit_logs (job_id, action, actor, comment) VALUES (?, ?, ?, ?)", (job_id, "drafted", "docusync", draft.summary))
    except Exception as exc:
        with connect() as conn:
            conn.execute("UPDATE jobs SET status=?, error=?, updated_at=? WHERE id=?", ("failed", str(exc), now_iso(), job_id))
            conn.execute("INSERT INTO audit_logs (job_id, action, actor, comment) VALUES (?, ?, ?, ?)", (job_id, "failed", "docusync", str(exc)))


def list_jobs() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        return [normalize_job(dict(row)) for row in rows]


def get_job(job_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        job = row_to_dict(row)
        if not job:
            return None
        logs = conn.execute("SELECT * FROM audit_logs WHERE job_id=? ORDER BY created_at ASC", (job_id,)).fetchall()
        job["audit_logs"] = [dict(log) for log in logs]
        return normalize_job(job)


async def approve_job(job_id: int, final_content: str, reviewer: str, comment: str | None) -> dict:
    job = get_job(job_id)
    if not job:
        raise ValueError("Job not found.")
    target_id = job.get("notion_target_id")
    if not target_id:
        raise ValueError("Job has no Notion target.")
    await NotionClient(get_settings()).publish_markdown(target_id, final_content)
    with connect() as conn:
        conn.execute(
            "UPDATE jobs SET status=?, final_content=?, published_at=?, updated_at=? WHERE id=?",
            ("published", final_content, now_iso(), now_iso(), job_id),
        )
        conn.execute("INSERT INTO audit_logs (job_id, action, actor, comment) VALUES (?, ?, ?, ?)", (job_id, "approved", reviewer, comment or "Approved and published."))
    return get_job(job_id) or {}


def reject_job(job_id: int, reviewer: str, comment: str) -> dict:
    job = get_job(job_id)
    if not job:
        raise ValueError("Job not found.")
    with connect() as conn:
        conn.execute("UPDATE jobs SET status=?, updated_at=? WHERE id=?", ("rejected", now_iso(), job_id))
        conn.execute("INSERT INTO audit_logs (job_id, action, actor, comment) VALUES (?, ?, ?, ?)", (job_id, "rejected", reviewer, comment))
    return get_job(job_id) or {}


def normalize_job(job: dict) -> dict:
    if isinstance(job.get("changed_files"), str):
        try:
            job["changed_files"] = json.loads(job["changed_files"])
        except json.JSONDecodeError:
            job["changed_files"] = []
    return job
