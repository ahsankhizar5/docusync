from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .models import DemoJobRequest, ReviewApproveRequest, ReviewRejectRequest
from .services.demo import build_demo_event
from .services.github import is_merged_pull_request, parse_pull_request_event, verify_signature
from .services.jobs import approve_job, clear_failed_jobs, create_job, get_job, list_jobs, process_job, reject_job
from .services.setup_status import get_setup_status
from .settings import get_settings


settings = get_settings()
app = FastAPI(title="DocuSync API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/setup/status")
def setup_status() -> dict:
    return get_setup_status(settings)


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
) -> dict:
    raw_body = await request.body()
    if not verify_signature(raw_body, x_hub_signature_256, settings.github_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature.")
    payload = await request.json()
    if not is_merged_pull_request(payload):
        return {"accepted": False, "reason": "Ignored non-merged pull request event."}
    event = await parse_pull_request_event(payload, settings.github_token)
    job_id = create_job(event)
    background_tasks.add_task(process_job, job_id)
    return {"accepted": True, "job_id": job_id}


@app.post("/api/demo/jobs")
async def demo_job(request: DemoJobRequest, background_tasks: BackgroundTasks) -> dict:
    event = build_demo_event(request)
    job_id = create_job(event)
    background_tasks.add_task(process_job, job_id)
    return {"accepted": True, "job_id": job_id, "title": event.pr_title}


@app.get("/api/jobs")
def api_list_jobs(
    include_failed: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[dict]:
    return list_jobs(include_failed=include_failed, limit=limit)


@app.delete("/api/jobs/failed")
def api_clear_failed_jobs() -> dict:
    deleted = clear_failed_jobs()
    return {"deleted": deleted}


@app.get("/api/jobs/{job_id}")
def api_get_job(job_id: int) -> dict:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.post("/api/jobs/{job_id}/approve")
async def api_approve_job(job_id: int, request: ReviewApproveRequest) -> dict:
    try:
        return await approve_job(job_id, request.final_content, request.reviewer, request.comment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/jobs/{job_id}/reject")
def api_reject_job(job_id: int, request: ReviewRejectRequest) -> dict:
    try:
        return reject_job(job_id, request.reviewer, request.comment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc



//
