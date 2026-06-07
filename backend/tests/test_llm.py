import pytest

import httpx
import pytest

from app.services.llm import extract_gemini_text, parse_draft_json, post_with_retries, strip_json_fences


def test_parse_draft_json_accepts_required_shape():
    draft = parse_draft_json('{"summary":"s","patch":"# Docs","confidence":0.8,"reviewer_notes":"check"}')

    assert draft.summary == "s"
    assert draft.confidence == 0.8


def test_parse_draft_json_rejects_missing_keys():
    with pytest.raises(ValueError):
        parse_draft_json('{"summary":"s"}')


def test_strip_json_fences_handles_markdown_response():
    assert strip_json_fences('```json\n{"ok": true}\n```') == '{"ok": true}'


def test_extract_gemini_text_reads_first_candidate_parts():
    payload = {"candidates": [{"content": {"parts": [{"text": '{"summary":'} , {"text": '"ok"}'}]}}]}

    assert extract_gemini_text(payload) == '{"summary":"ok"}'


@pytest.mark.anyio
async def test_post_with_retries_recovers_from_transient_error(monkeypatch):
    calls = {"count": 0}

    async def fake_post(*args, **kwargs):
        calls["count"] += 1
        status = 503 if calls["count"] == 1 else 200
        return httpx.Response(status, json={"ok": True}, request=httpx.Request("POST", "https://example.test"))

    async def fake_sleep(_seconds):
        return None

    client = httpx.AsyncClient()
    monkeypatch.setattr(client, "post", fake_post)
    monkeypatch.setattr("app.services.llm.asyncio.sleep", fake_sleep)

    response = await post_with_retries(client, "https://example.test", headers={}, payload={})

    assert response.status_code == 200
    assert calls["count"] == 2
