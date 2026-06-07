# Deployment Guide

## Backend: Render

1. Push this project to `https://github.com/ahsankhizar5/docusync`.
2. In Render, create a new Blueprint or Web Service from the repository.
3. Use `render.yaml` if creating from Blueprint.
4. Set these secret environment variables in Render:
   - `GEMINI_API_KEY`
   - `NOTION_API_KEY`
   - `GITHUB_WEBHOOK_SECRET`
5. Set `CORS_ORIGINS` to the deployed Vercel URL, for example `https://your-app.vercel.app`.
6. Copy the Render backend URL for GitHub and Vercel configuration.

## Frontend: Vercel

1. Import the GitHub repository into Vercel.
2. Set the project root to `frontend`.
3. Add this environment variable:
   - `NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com`
4. Deploy.

## GitHub Webhook

Create a repository webhook for `https://your-render-service.onrender.com/webhooks/github`.

- Content type: `application/json`
- Secret: same value as `GITHUB_WEBHOOK_SECRET`
- Events: Pull requests

## Notion

Share each target documentation page with the Notion integration. Replace demo target IDs in `config/module_mapping.json` with real Notion block or page IDs.
