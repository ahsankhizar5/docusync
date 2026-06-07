import re
from typing import Any

import httpx

from ..settings import Settings


class NotionClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.enabled = bool(settings.notion_api_key)

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.notion_api_key}",
            "Notion-Version": self.settings.notion_version,
            "Content-Type": "application/json",
        }

    async def retrieve_markdown(self, target_id: str, fallback_docs: str) -> str:
        normalized_target_id = normalize_notion_id(target_id)
        if not self.enabled or normalized_target_id.startswith("demo-"):
            return fallback_docs
        url = f"https://api.notion.com/v1/blocks/{normalized_target_id}/children?page_size=100"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            markdown = blocks_to_markdown(response.json().get("results", []))
            return markdown or fallback_docs

    async def publish_markdown(self, target_id: str, markdown: str) -> None:
        normalized_target_id = normalize_notion_id(target_id)
        if not self.enabled or normalized_target_id.startswith("demo-"):
            return
        children = markdown_to_notion_blocks(markdown)
        url = f"https://api.notion.com/v1/blocks/{normalized_target_id}/children"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.patch(url, headers=self.headers, json={"children": children})
            response.raise_for_status()


def normalize_notion_id(value: str) -> str:
    cleaned = value.strip()
    match = re.search(r"([0-9a-fA-F]{32})", cleaned.replace("-", ""))
    if not match:
        return cleaned
    raw = match.group(1).lower()
    return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


def blocks_to_markdown(blocks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for block in blocks:
        block_type = block.get("type")
        content = block.get(block_type, {}) if block_type else {}
        text = rich_text_to_plain(content.get("rich_text", []))
        if not text:
            continue
        if block_type == "heading_1":
            lines.append(f"# {text}")
        elif block_type == "heading_2":
            lines.append(f"## {text}")
        elif block_type == "heading_3":
            lines.append(f"### {text}")
        elif block_type == "bulleted_list_item":
            lines.append(f"- {text}")
        elif block_type == "numbered_list_item":
            lines.append(f"1. {text}")
        else:
            lines.append(text)
    return "\n".join(lines).strip()


def rich_text_to_plain(items: list[dict[str, Any]]) -> str:
    return "".join((item.get("plain_text") or "") for item in items)


def markdown_to_notion_blocks(markdown: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        block_type = "paragraph"
        text = line
        if line.startswith("### "):
            block_type, text = "heading_3", line[4:]
        elif line.startswith("## "):
            block_type, text = "heading_2", line[3:]
        elif line.startswith("# "):
            block_type, text = "heading_1", line[2:]
        elif line.startswith("- "):
            block_type, text = "bulleted_list_item", line[2:]
        blocks.append({
            "object": "block",
            "type": block_type,
            block_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
        })
    return blocks
