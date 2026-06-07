import hmac
import hashlib
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class PullRequestEvent:
    repo_full_name: str
    pr_number: int
    pr_title: str
    pr_body: str
    pr_url: str | None
    merged_by: str | None
    changed_files: list[str]
    diff: str


def verify_signature(raw_body: bytes, signature_header: str | None, secret: str) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def is_merged_pull_request(payload: dict[str, Any]) -> bool:
    return (
        payload.get("action") == "closed"
        and payload.get("pull_request", {}).get("merged") is True
    )


async def fetch_pr_diff(diff_url: str | None, github_token: str | None) -> str:
    if not diff_url:
        return ""
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(diff_url, headers=headers)
        response.raise_for_status()
        return response.text


async def parse_pull_request_event(payload: dict[str, Any], github_token: str | None) -> PullRequestEvent:
    pr = payload["pull_request"]
    repo = payload["repository"]
    files = []
    if pr.get("changed_files"):
        files = [item.get("filename", "") for item in payload.get("files", []) if item.get("filename")]
    diff = payload.get("diff") or await fetch_pr_diff(pr.get("diff_url"), github_token)
    if not files:
        files = extract_changed_files_from_diff(diff)
    return PullRequestEvent(
        repo_full_name=repo["full_name"],
        pr_number=pr["number"],
        pr_title=pr.get("title") or "",
        pr_body=pr.get("body") or "",
        pr_url=pr.get("html_url"),
        merged_by=(pr.get("merged_by") or {}).get("login"),
        changed_files=files,
        diff=diff,
    )


def extract_changed_files_from_diff(diff: str) -> list[str]:
    files: list[str] = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" ")
            if len(parts) >= 4:
                files.append(parts[2].removeprefix("a/"))
    return files
