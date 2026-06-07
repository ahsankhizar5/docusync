import pytest

from app.services.github import PullRequestEvent
from app.services.jobs import create_job, get_job, process_job


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
        pr_body="Implements 15-minute reset token expiry.",
        pr_url=None,
        merged_by="demo-user",
        changed_files=["src/auth/reset_password.py"],
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
