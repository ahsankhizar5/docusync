from app.models import DemoJobRequest
from app.services.demo import build_demo_event


def test_demo_event_uses_unique_title_suffix():
    first = build_demo_event(DemoJobRequest())
    second = build_demo_event(DemoJobRequest())

    assert first.pr_title != second.pr_title
    assert first.pr_number != second.pr_number


def test_demo_event_respects_custom_request_values():
    event = build_demo_event(
        DemoJobRequest(
            repo_full_name="custom/repo",
            pr_number=44,
            pr_title="Custom demo",
            pr_body="Custom body",
            changed_files=["frontend/app/page.tsx"],
            diff="+ custom",
        )
    )

    assert event.repo_full_name == "custom/repo"
    assert event.pr_number == 44
    assert event.pr_title == "Custom demo"
    assert event.pr_body == "Custom body"
    assert event.changed_files == ["frontend/app/page.tsx"]
    assert event.diff == "+ custom"
