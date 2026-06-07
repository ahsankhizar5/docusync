import hashlib
import hmac

from app.services.github import extract_changed_files_from_diff, is_merged_pull_request, verify_signature


def test_verify_signature_accepts_valid_sha256_signature():
    body = b'{"ok": true}'
    secret = "dev-secret"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert verify_signature(body, signature, secret) is True


def test_verify_signature_rejects_invalid_signature():
    assert verify_signature(b"{}", "sha256=bad", "dev-secret") is False


def test_is_merged_pull_request_only_accepts_closed_and_merged():
    assert is_merged_pull_request({"action": "closed", "pull_request": {"merged": True}}) is True
    assert is_merged_pull_request({"action": "opened", "pull_request": {"merged": False}}) is False


def test_extract_changed_files_from_diff():
    diff = "diff --git a/src/auth/reset.py b/src/auth/reset.py\n@@\n+new line"

    assert extract_changed_files_from_diff(diff) == ["src/auth/reset.py"]
