import pytest
from sqlalchemy import update

from app.database import get_engine, jobs
from app.services.github import PullRequestEvent
from app.services.jobs import clear_failed_jobs, create_job, get_job, list_jobs, process_job


@pytest.mark.anyio
async def test_process_job_reaches_review_state(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MODULE_MAPPING_PATH", "../config/module_mapping.json")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    from app.settings import get_settings

    get_settings.cache_clear()
    event = PullRequestEvent(
        repo_full_name="demo/docusync-target",
        pr_number=1,
        pr_title="Add password reset expiry policy",
        pr_body="Implements 15-minute reset expiry.",
        pr_url=None,
        merged_by="demo-user",
        changed_files=["backend/app/services/auth.py"],
        diff="+ create_reset_token(user, expires_in_minutes=15)",
    )

    job_id = create_job(event)
    await process_job(job_id)
    job = get_job(job_id)

    assert job is not None
    assert job["status"] == "awaiting_review"
    assert job["mapped_module"] == "Backend API"
    assert "Latest synchronized change" in job["ai_patch"]

    get_settings.cache_clear()


def test_list_jobs_hides_failed_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    from app.settings import get_settings

    get_settings.cache_clear()
    first_id = create_job(
        PullRequestEvent(
            repo_full_name="demo/docusync-target",
            pr_number=1,
            pr_title="Failed job",
            pr_body="",
            pr_url=None,
            merged_by="demo-user",
            changed_files=["unknown/file.py"],
            diff="+ no mapping",
        )
    )
    create_job(
        PullRequestEvent(
            repo_full_name="demo/docusync-target",
            pr_number=2,
            pr_title="Visible job",
            pr_body="",
            pr_url=None,
            merged_by="demo-user",
            changed_files=["backend/app/main.py"],
            diff="+ mapped",
        )
    )
    with get_engine().begin() as conn:
        conn.execute(update(jobs).where(jobs.c.id == first_id).values(status="failed"))

    visible_titles = [job["pr_title"] for job in list_jobs()]
    all_titles = [job["pr_title"] for job in list_jobs(include_failed=True)]

    assert visible_titles == ["Visible job"]
    assert all_titles == ["Visible job", "Failed job"]

    get_settings.cache_clear()


def test_clear_failed_jobs_deletes_only_failed_rows(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    from app.settings import get_settings

    get_settings.cache_clear()
    failed_id = create_job(
        PullRequestEvent(
            repo_full_name="demo/docusync-target",
            pr_number=1,
            pr_title="Failed job",
            pr_body="",
            pr_url=None,
            merged_by="demo-user",
            changed_files=["unknown/file.py"],
            diff="+ no mapping",
        )
    )
    create_job(
        PullRequestEvent(
            repo_full_name="demo/docusync-target",
            pr_number=2,
            pr_title="Queued job",
            pr_body="",
            pr_url=None,
            merged_by="demo-user",
            changed_files=["backend/app/main.py"],
            diff="+ mapped",
        )
    )
    with get_engine().begin() as conn:
        conn.execute(update(jobs).where(jobs.c.id == failed_id).values(status="failed"))

    assert clear_failed_jobs() == 1
    assert [job["pr_title"] for job in list_jobs(include_failed=True)] == ["Queued job"]

    get_settings.cache_clear()
