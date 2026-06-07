import json
import asyncio
from dataclasses import dataclass

import httpx

from ..settings import Settings


@dataclass
class DocumentationDraft:
    summary: str
    patch: str
    confidence: float
    reviewer_notes: str


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, current_docs: str, pr_title: str, pr_body: str, diff: str) -> DocumentationDraft:
        provider = self.settings.llm_provider.lower()
        if provider == "openai" and self.settings.openai_api_key:
            return await self._openai(current_docs, pr_title, pr_body, diff)
        if provider == "gemini" and self.settings.gemini_api_key:
            return await self._gemini(current_docs, pr_title, pr_body, diff)
        return self._mock(current_docs, pr_title, pr_body, diff)

    async def _openai(self, current_docs: str, pr_title: str, pr_body: str, diff: str) -> DocumentationDraft:
        prompt = build_prompt(current_docs, pr_title, pr_body, diff)
        payload = {
            "model": self.settings.openai_model,
            "messages": [
                {"role": "system", "content": "You are DocuSync, a cautious software documentation maintenance agent."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": self.settings.llm_temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return parse_draft_json(content)

    async def _gemini(self, current_docs: str, pr_title: str, pr_body: str, diff: str) -> DocumentationDraft:
        prompt = build_prompt(current_docs, pr_title, pr_body, diff)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:generateContent"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": self.settings.llm_temperature,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "summary": {"type": "STRING"},
                        "patch": {"type": "STRING"},
                        "confidence": {"type": "NUMBER"},
                        "reviewer_notes": {"type": "STRING"},
                    },
                    "required": ["summary", "patch", "confidence", "reviewer_notes"],
                },
            },
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.settings.gemini_api_key,
        }
        async with httpx.AsyncClient(timeout=45) as client:
            response = await post_with_retries(client, url, headers=headers, payload=payload)
        content = extract_gemini_text(response.json())
        return parse_draft_json(content)

    def _mock(self, current_docs: str, pr_title: str, pr_body: str, diff: str) -> DocumentationDraft:
        signal = "functional behavior change" if any(token in diff.lower() for token in ["expires", "return", "endpoint", "permission", "auth"]) else "possible code change"
        patch = f"""{current_docs.rstrip()}

## Latest synchronized change
{pr_title}

DocuSync detected a {signal} from the merged pull request. Reviewer should verify the business impact before publishing.

Developer context: {pr_body or "No pull request description was provided."}
"""
        return DocumentationDraft(
            summary=f"Drafted documentation update for: {pr_title}",
            patch=patch.strip(),
            confidence=0.72 if signal.startswith("functional") else 0.48,
            reviewer_notes="Mock provider used. Configure LLM_PROVIDER=gemini and GEMINI_API_KEY for live model reasoning.",
        )


def build_prompt(current_docs: str, pr_title: str, pr_body: str, diff: str) -> str:
    return f"""
Current documentation:
{current_docs}

Merged pull request title:
{pr_title}

Merged pull request description:
{pr_body}

Unified diff:
{diff}

Return JSON with exactly these keys:
summary: concise description of the required documentation update.
patch: complete Markdown replacement for the relevant documentation section.
confidence: number from 0 to 1.
reviewer_notes: concise warnings about uncertain business impact.

Only document functional behavior, product-visible flows, integration contracts, or operational rules.
Ignore formatting-only refactors and unsupported performance claims.
""".strip()


def parse_draft_json(content: str) -> DocumentationDraft:
    data = json.loads(strip_json_fences(content))
    for key in ["summary", "patch", "confidence", "reviewer_notes"]:
        if key not in data:
            raise ValueError(f"LLM output missing required key: {key}")
    return DocumentationDraft(
        summary=str(data["summary"]),
        patch=str(data["patch"]),
        confidence=float(data["confidence"]),
        reviewer_notes=str(data["reviewer_notes"]),
    )


def extract_gemini_text(payload: dict) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini response did not include candidates.")
    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts)
    if not text.strip():
        raise ValueError("Gemini response did not include text content.")
    return text


def strip_json_fences(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


async def post_with_retries(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    payload: dict,
    attempts: int = 3,
) -> httpx.Response:
    last_response: httpx.Response | None = None
    for attempt in range(attempts):
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code not in {429, 500, 502, 503, 504}:
            response.raise_for_status()
            return response
        last_response = response
        if attempt < attempts - 1:
            await asyncio.sleep(1.5 * (attempt + 1))
    assert last_response is not None
    last_response.raise_for_status()
    return last_response
