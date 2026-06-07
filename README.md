---
title: Phenom PM Intelligence
emoji: 🧭
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Phenom PM Intelligence Tool

Research a prospect's talent operations and generate a tailored Phenom sales pitch.
Enter a company name → live web research (Tavily) → analysis & pitch (Claude).

## Architecture

- **Frontend** — React + Vite SPA (`frontend/`), built to static assets.
- **Backend** — FastAPI (`backend/`): the 5-stage research pipeline + Claude synthesis.
- In production a single container serves both: FastAPI hosts the built frontend
  and the `/api` routes on the same origin.

## Run locally

Backend (from the repo root):

```bash
pip install -r backend/requirements.txt
uvicorn api:app --app-dir backend --reload --port 8000
```

Frontend (dev server with proxy to :8000):

```bash
cd frontend && npm install && npm run dev
```

## Configuration

Set these as environment variables (locally via `backend/.env`, on Hugging Face
via **Space → Settings → Secrets**):

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude synthesis (required) |
| `TAVILY_API_KEY` | Live web research (required) |
| `PHENOM_LLM_PROVIDER` | `anthropic` (default) |
| `PHENOM_SEARCH_PROVIDER` | `tavily` (default) |

## Deploy (Hugging Face Docker Space)

The repo root `Dockerfile` builds the frontend and serves everything via uvicorn
on port `7860`. Push this repo to a Docker Space and add the two API keys as
Space secrets.
