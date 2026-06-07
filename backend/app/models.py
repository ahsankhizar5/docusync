from pydantic import BaseModel, Field


class ReviewApproveRequest(BaseModel):
    final_content: str = Field(..., min_length=1)
    reviewer: str = "reviewer"
    comment: str | None = None


class ReviewRejectRequest(BaseModel):
    reviewer: str = "reviewer"
    comment: str = Field(..., min_length=1)


class DemoJobRequest(BaseModel):
    repo_full_name: str | None = None
    pr_number: int | None = None
    pr_title: str | None = None
    pr_body: str | None = None
    changed_files: list[str] | None = None
    diff: str | None = None
