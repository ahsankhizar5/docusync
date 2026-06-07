from pydantic import BaseModel, Field


class ReviewApproveRequest(BaseModel):
    final_content: str = Field(..., min_length=1)
    reviewer: str = "reviewer"
    comment: str | None = None


class ReviewRejectRequest(BaseModel):
    reviewer: str = "reviewer"
    comment: str = Field(..., min_length=1)


class DemoJobRequest(BaseModel):
    repo_full_name: str = "demo/docusync-target"
    pr_number: int = 1
    pr_title: str = "Add password reset expiry policy"
    pr_body: str = "Implements 15-minute reset token expiry and invalidates used tokens."
    changed_files: list[str] = Field(default_factory=lambda: ["src/auth/reset_password.py"])
    diff: str = """diff --git a/src/auth/reset_password.py b/src/auth/reset_password.py
@@
- token = create_reset_token(user)
+ token = create_reset_token(user, expires_in_minutes=15)
+ mark_reset_token_used(token)
"""
