import json
from datetime import datetime, timezone

from sqlalchemy import delete, desc, insert, select, update

from ..database import audit_logs, get_engine, jobs
from ..settings import get_settings
from .github import PullRequestEvent
from .llm import LLMClient
from .mapping import load_mappings, select_mapping
from .notion import NotionClient


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_job(event: PullRequestEvent) -> int:
    with get_engine().begin() as conn:
        result = conn.execute(
            insert(jobs).values(
                status="queued",
                repo_full_name=event.repo_full_name,
                pr_number=event.pr_number,
                pr_title=event.pr_title,
                pr_url=event.pr_url,
                pr_body=event.pr_body,
                merged_by=event.merged_by,
                changed_files=json.dumps(event.changed_files),
                diff=event.diff,
                updated_at=now_utc(),
            )
        )
        job_id = int(result.inserted_primary_key[0])
        conn.execute(
            insert(audit_logs).values(
                job_id=job_id,
                action="queued",
                actor="github",
                comment="Webhook event accepted.",
            )
        )
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
        with get_engine().begin() as conn:
            conn.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    status="awaiting_review",
                    mapped_module=mapping.module,
                    notion_target_id=mapping.notion_target_id,
                    current_docs=current_docs,
                    ai_summary=draft.summary,
                    ai_patch=draft.patch,
                    ai_confidence=draft.confidence,
                    reviewer_notes=draft.reviewer_notes,
                    updated_at=now_utc(),
                )
            )
            conn.execute(insert(audit_logs).values(job_id=job_id, action="drafted", actor="docusync", comment=draft.summary))
    except Exception as exc:
        with get_engine().begin() as conn:
            conn.execute(update(jobs).where(jobs.c.id == job_id).values(status="failed", error=str(exc), updated_at=now_utc()))
            conn.execute(insert(audit_logs).values(job_id=job_id, action="failed", actor="docusync", comment=str(exc)))


JOB_SUMMARY_COLUMNS = [
    jobs.c.id,
    jobs.c.status,
    jobs.c.repo_full_name,
    jobs.c.pr_number,
    jobs.c.pr_title,
    jobs.c.pr_url,
    jobs.c.merged_by,
    jobs.c.mapped_module,
    jobs.c.ai_summary,
    jobs.c.ai_confidence,
    jobs.c.error,
    jobs.c.created_at,
    jobs.c.updated_at,
    jobs.c.published_at,
]


def list_jobs(include_failed: bool = False, limit: int = 50) -> list[dict]:
    with get_engine().begin() as conn:
        query = select(*JOB_SUMMARY_COLUMNS).order_by(desc(jobs.c.created_at), desc(jobs.c.id)).limit(limit)
        if not include_failed:
            query = query.where(jobs.c.status != "failed")
        rows = conn.execute(query).mappings().fetchall()
        return [normalize_job(dict(row)) for row in rows]


def clear_failed_jobs() -> int:
    with get_engine().begin() as conn:
        result = conn.execute(delete(jobs).where(jobs.c.status == "failed"))
        return int(result.rowcount or 0)


def get_job(job_id: int) -> dict | None:
    with get_engine().begin() as conn:
        row = conn.execute(select(jobs).where(jobs.c.id == job_id)).mappings().fetchone()
        job = dict(row) if row is not None else None
        if not job:
            return None
        logs = conn.execute(
            select(audit_logs).where(audit_logs.c.job_id == job_id).order_by(audit_logs.c.created_at.asc())
        ).mappings().fetchall()
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
    with get_engine().begin() as conn:
        conn.execute(
            update(jobs)
            .where(jobs.c.id == job_id)
            .values(status="published", final_content=final_content, published_at=now_utc(), updated_at=now_utc())
        )
        conn.execute(insert(audit_logs).values(job_id=job_id, action="approved", actor=reviewer, comment=comment or "Approved and published."))
    return get_job(job_id) or {}


def reject_job(job_id: int, reviewer: str, comment: str) -> dict:
    job = get_job(job_id)
    if not job:
        raise ValueError("Job not found.")
    with get_engine().begin() as conn:
        conn.execute(update(jobs).where(jobs.c.id == job_id).values(status="rejected", updated_at=now_utc()))
        conn.execute(insert(audit_logs).values(job_id=job_id, action="rejected", actor=reviewer, comment=comment))
    return get_job(job_id) or {}


def normalize_job(job: dict) -> dict:
    if isinstance(job.get("changed_files"), str):
        try:
            job["changed_files"] = json.loads(job["changed_files"])
        except json.JSONDecodeError:
            job["changed_files"] = []
    return job
