# DocuSync Production Onboarding

This document is the handoff checklist for turning DocuSync from a mock demo into a production-grade system.

## ELI10 Version

DocuSync needs permission to talk to three outside systems:

1. **The brain**: an LLM provider such as OpenAI, Gemini, or Anthropic.
2. **The code trigger**: GitHub, so DocuSync knows when a pull request is merged.
3. **The document home**: Notion, so DocuSync can read and update documentation.

Do not paste secret keys into chat. Put secret values only in `backend/.env` locally or in a real secrets manager when deployed.

## What You Can Safely Tell The Developer In Chat

- Which LLM provider you want to use first: `openai`, `gemini`, or `anthropic`.
- Your GitHub repository URL, for example `https://github.com/org/repo`.
- The names of the modules you want DocuSync to track, for example `Authentication`, `Billing`, `API`.
- The code path for each module, for example `src/auth/`.
- The Notion page name for each module.
- Whether this is for local demo, staging, or production deployment.
- The hosting preference, for example Render, Railway, AWS, Azure, GCP, or university/local server.

## What You Should Not Paste In Chat

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`
- `NOTION_API_KEY`
- `GITHUB_WEBHOOK_SECRET`
- GitHub personal access tokens
- Private repository source code
- Production Notion private content unless you explicitly intend to share it

## Secrets To Put In `backend/.env`

```env
GITHUB_WEBHOOK_SECRET=
GITHUB_TOKEN=
LLM_PROVIDER=openai
OPENAI_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
NOTION_API_KEY=
NOTION_DATABASE_OR_PAGE_ID=
MODULE_MAPPING_PATH=../config/module_mapping.json
DATABASE_PATH=./docusync.db
```

Only fill the key for the provider you choose. For example, if `LLM_PROVIDER=openai`, fill `OPENAI_API_KEY` and leave Gemini/Anthropic empty.

## Provider Options

### Option 1: OpenAI

Best default for a production DocuSync build because it has strong structured output support, production guidance, project-level API keys, usage controls, and safety guidance.

Use when you want the safest first enterprise path.

### Option 2: Google Gemini

Good when you need very large context windows for big diffs, PDFs, or large documentation pages. It also supports structured outputs and has strong multimodal options.

Use when your pull requests or docs are very large.

### Option 3: Anthropic Claude

Good for code-heavy reasoning and enterprise deployments, especially if the team already uses Claude, Bedrock, or Vertex AI.

Use when your organization prefers Claude or wants cloud-provider-managed access through AWS/GCP.

## Production Upgrade Checklist

- Use Supabase PostgreSQL through `DATABASE_URL`.
- Replace in-process background tasks with a worker queue such as Celery/RQ plus Redis.
- Add login and role-based access control for reviewers.
- Add organization/project/workspace separation.
- Add webhook delivery logs and retry handling.
- Add GitHub App support instead of only repository webhooks.
- Add real PR file listing and diff fetching through GitHub API.
- Add Notion page/block update strategy that edits the correct section instead of appending blindly.
- Add provider adapters for OpenAI, Gemini, and Anthropic.
- Add prompt/version management and evaluation datasets.
- Add metrics: latency, token usage, cost, approval rate, rejection rate, hallucination rate.
- Add Dockerfiles and deployment configuration.
- Move secrets to a deployment secret manager.
- Add rate limits, request size limits, and audit export.

## Recommended First Production Sequence

1. Choose the LLM provider.
2. Fill local `.env` with the chosen provider key.
3. Create the Notion integration and share the target documentation pages with it.
4. Replace demo Notion IDs in `config/module_mapping.json`.
5. Configure a GitHub webhook with a secret.
6. Test one real merged pull request.
7. Upgrade storage and worker queue.
8. Add reviewer login and enterprise dashboard features.
9. Deploy frontend and backend as separate Vercel projects.
10. Run evaluation scenarios and write the paper results section.
