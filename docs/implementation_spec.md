# DocuSync Module 2 Implementation Specification

## Objective

DocuSync implements the proposed Assignment 1 system as a production-style academic demo. Its main workflow is:

GitHub merged pull request -> FastAPI webhook -> PR metadata and diff extraction -> module-to-documentation mapping -> Notion documentation retrieval -> LLM-generated Markdown update -> human review dashboard -> approved Notion publication.

## Backend Behavior

- `POST /webhooks/github` verifies `X-Hub-Signature-256`, ignores non-merged pull requests, stores merged PR jobs, and starts processing.
- `POST /api/demo/jobs` creates a local demo job without GitHub, useful for classroom demonstration and testing.
- `GET /api/jobs` and `GET /api/jobs/{id}` power the reviewer dashboard.
- `POST /api/jobs/{id}/approve` publishes reviewer-approved Markdown to Notion and stores the final content.
- `POST /api/jobs/{id}/reject` records the reviewer comment without publishing.

## Data Model

Each job stores PR identity, changed files, unified diff, mapped module, Notion target, current docs, AI summary, AI patch, confidence, reviewer notes, final reviewer content, status, errors, timestamps, and audit logs.

Primary statuses:

- `queued`
- `awaiting_review`
- `published`
- `rejected`
- `failed`

## Integration Strategy

- GitHub integration is real: HMAC verification is required for `/webhooks/github`.
- Notion integration is real when `NOTION_API_KEY` and non-demo target IDs are configured.
- LLM integration is provider-based. `LLM_PROVIDER=mock` supports development and demos without paid API calls. `LLM_PROVIDER=openai` uses OpenAI chat completions and requires `OPENAI_API_KEY`.

## Demo Scenario

1. Start backend and frontend locally.
2. Create a demo job from the dashboard or merge a PR in a test GitHub repository.
3. Confirm the job reaches `awaiting_review`.
4. Open the job detail view and inspect PR metadata, changed files, current docs, proposed docs, confidence, and reviewer notes.
5. Approve with or without edits, then show final `published` state.
6. For real Notion targets, verify the approved content appears in Notion.

## Evaluation Metrics

- Semantic correctness: reviewer score for whether the proposed update matches the code change.
- Completeness: reviewer score for whether all user-visible behavior changes are covered.
- Hallucination rate: percentage of drafts containing unsupported business claims.
- Reviewer edit distance: how much final content differs from AI draft.
- Approval/rejection rate: percentage of drafts accepted without rejection.
- Time saved: estimated manual documentation time minus review/edit time.
