from ..settings import Settings


def get_setup_status(settings: Settings) -> dict:
    provider = settings.llm_provider.lower()
    provider_key_map = {
        "openai": bool(settings.openai_api_key),
        "gemini": bool(settings.gemini_api_key),
        "anthropic": bool(settings.anthropic_api_key),
        "mock": True,
    }
    checks = [
        {
            "id": "llm_provider",
            "label": "LLM provider",
            "configured": provider in provider_key_map,
            "detail": provider,
        },
        {
            "id": "llm_key",
            "label": f"{provider.title()} API key",
            "configured": provider_key_map.get(provider, False),
            "detail": "Set in backend environment" if provider_key_map.get(provider, False) else "Missing provider API key",
        },
        {
            "id": "notion_key",
            "label": "Notion API key",
            "configured": bool(settings.notion_api_key),
            "detail": "Set in backend environment" if settings.notion_api_key else "Missing NOTION_API_KEY",
        },
        {
            "id": "notion_target",
            "label": "Notion docs target",
            "configured": bool(settings.notion_database_or_page_id),
            "detail": "Set in backend environment" if settings.notion_database_or_page_id else "Missing NOTION_DATABASE_OR_PAGE_ID",
        },
        {
            "id": "github_secret",
            "label": "GitHub webhook secret",
            "configured": bool(settings.github_webhook_secret and settings.github_webhook_secret != "dev-secret" and "replace" not in settings.github_webhook_secret),
            "detail": "Custom secret configured" if settings.github_webhook_secret and settings.github_webhook_secret != "dev-secret" else "Use a custom production secret",
        },
        {
            "id": "module_mapping",
            "label": "Module mapping file",
            "configured": settings.module_mapping_file.exists(),
            "detail": str(settings.module_mapping_file),
        },
    ]
    return {
        "environment": "production-ready" if all(check["configured"] for check in checks) else "setup-required",
        "checks": checks,
        "deployment": {
            "frontend": "Vercel",
            "backend": "Vercel",
            "github_repo": "https://github.com/ahsankhizar5/docusync",
        },
    }
