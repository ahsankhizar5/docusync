from app.services.notion import blocks_to_markdown, markdown_to_notion_blocks, normalize_notion_id


def test_blocks_to_markdown_converts_basic_blocks():
    blocks = [
        {"type": "heading_1", "heading_1": {"rich_text": [{"plain_text": "Auth"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Reset tokens expire."}]}},
    ]

    assert blocks_to_markdown(blocks) == "# Auth\nReset tokens expire."


def test_blocks_to_markdown_returns_empty_for_empty_page():
    assert blocks_to_markdown([]) == ""


def test_markdown_to_notion_blocks_converts_headings_and_bullets():
    blocks = markdown_to_notion_blocks("# Auth\n- Reset tokens expire.")

    assert blocks[0]["type"] == "heading_1"
    assert blocks[1]["type"] == "bulleted_list_item"


def test_normalize_notion_id_extracts_page_id_from_url():
    url = "https://app.notion.com/p/Backend-API-Docs-378e7c1d9c0480f0b8fbc2560b6b0f96"

    assert normalize_notion_id(url) == "378e7c1d-9c04-80f0-b8fb-c2560b6b0f96"


def test_normalize_notion_id_keeps_demo_targets():
    assert normalize_notion_id("demo-auth-docs") == "demo-auth-docs"
