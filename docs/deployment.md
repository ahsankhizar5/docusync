# Deployment Guide

DocuSync production uses:

- Frontend: Vercel project with root directory `frontend`
- Backend: Vercel project with root directory `backend`
- Database: Supabase PostgreSQL
- LLM: Gemini
- Documentation target: Notion

## Secret Safety

Do not commit database passwords or API keys. Store secrets only in local `backend/.env`, Vercel environment variables, or the provider secret manager.

If a database password or API key was pasted into chat, rotate it before deployment.

## Supabase Database

Set the Supabase connection strings as `DATABASE_URL` and `DIRECT_URL`.

- `DATABASE_URL`: transaction-mode pooler, used by the running app.
- `DIRECT_URL`: session-mode pooler, used by the initializer/migration script.

The Prisma snippet from Supabase includes `pgbouncer=true`; that flag is Prisma-specific. DocuSync strips it before connecting through Python/SQLAlchemy.

Local `backend/.env`:

```env
DATABASE_URL=postgresql://postgres.keumpxbhvlumvwnhcgce:<NEW-PASSWORD>@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?pgbouncer=true
DIRECT_URL=postgresql://postgres.keumpxbhvlumvwnhcgce:<NEW-PASSWORD>@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
```

After setting `DATABASE_URL`, initialize tables:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\init_db.py
```

This creates `jobs` and `audit_logs`.

## Vercel Multi-Service Setup

The repository root contains `vercel.json` with two services:

- `frontend` at route prefix `/`
- `backend` at route prefix `/_backend`

This file is required by Vercel when deploying both services from one repository. Without it, the Deploy button stays disabled.

## Backend: Vercel

Create a Vercel project from the GitHub repository:

- Root directory: `backend`
- Framework preset: Other

Set backend environment variables:

```env
DATABASE_URL=
DIRECT_URL=
GEMINI_API_KEY=
NOTION_API_KEY=
NOTION_DATABASE_OR_PAGE_ID=https://app.notion.com/p/DocuSync-Project-Docs-378e7c1d9c04806a9a33f596abdfb006
GITHUB_WEBHOOK_SECRET=
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
MODULE_MAPPING_PATH=../config/module_mapping.json
CORS_ORIGINS=https://your-frontend.vercel.app
```

The backend Vercel entrypoint is `backend/api/index.py`.

## Frontend: Vercel

Create a second Vercel project from the same GitHub repository:

- Root directory: `frontend`
- Framework preset: Next.js

Set frontend environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-app.vercel.app/_backend
NEXT_PUBLIC_SUPABASE_URL=https://keumpxbhvlumvwnhcgce.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
```

Supabase browser/server client helpers are available under `frontend/utils/supabase/`. Session-refresh middleware is staged as `frontend/middleware.ts.disabled`; rename it to `middleware.ts` when reviewer login/RBAC is implemented.

## GitHub Webhook

Create a repository webhook:

```text
https://your-app.vercel.app/_backend/webhooks/github
```

- Content type: `application/json`
- Secret: same value as `GITHUB_WEBHOOK_SECRET`
- Events: Pull requests

## Notion

Share each target documentation page with the Notion integration. The current mapping is stored in `config/module_mapping.json`.
