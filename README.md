# DocuSync

DocuSync is an LLM-assisted documentation synchronization system for AI Project Module 2. It receives GitHub merged pull request events, retrieves the relevant Notion documentation, generates a targeted Markdown update, and routes the draft through a human review dashboard before publishing.

## Project Layout

- `backend/`: FastAPI API, GitHub webhook receiver, LLM provider layer, Notion adapter, SQLite storage, tests.
- `frontend/`: Next.js review dashboard.
- `config/module_mapping.json`: maps changed code paths to Notion documentation targets.
- `docs/implementation_spec.md`: implementation and demo specification.

## Quick Start

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`, create a demo job, review the AI draft, then approve or reject it. With `LLM_PROVIDER=mock` and demo Notion targets, no external credentials are required. For the final full-integration demo, set real GitHub, OpenAI, and Notion credentials in `backend/.env`.

## GitHub Webhook

Configure GitHub to send `Pull requests` events to:

```text
POST https://your-public-url/webhooks/github
```

Use the same secret in GitHub and `GITHUB_WEBHOOK_SECRET`. For local testing, expose the backend with ngrok or a similar tunnel.

## Notion Setup

Create or choose Notion documentation pages, share them with your Notion integration, then replace each `notion_target_id` in `config/module_mapping.json` with the target block/page ID.

## Production Onboarding

Before adding real keys, read `docs/production_onboarding.md`. It explains what information can be shared in chat, what must stay secret, and what needs to be configured to move from demo mode to production mode.

## Deployment

The planned production deployment is Vercel for the Next.js dashboard and Render for the FastAPI backend. See `docs/deployment.md`.
