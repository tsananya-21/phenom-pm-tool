"""
FastAPI backend — thin wrapper around the existing pipeline and synthesis.
Start: uvicorn api:app --reload --port 8000
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.settings import load_config
from search.base import get_search_provider
from providers.base import get_llm_provider
from synthesis.synthesizer import synthesize

# Built frontend (copied here in the Docker image). Absent in local dev, where
# Vite serves the frontend and this stays API-only.
_STATIC_DIR = Path(__file__).parent / "static"

# Suggested companies for the "Try" row on the home page.
SUGGESTED_COMPANIES = ["Meta", "Apple", "Amazon", "Netflix", "Google", "Microsoft"]

app = FastAPI(title="Phenom PM Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cfg = load_config()
_search = get_search_provider(_cfg)
_llm = get_llm_provider(_cfg)


class ResearchRequest(BaseModel):
    company: str


@app.get("/api/companies")
def available_companies():
    return {"companies": SUGGESTED_COMPANIES}


@app.post("/api/research")
def research(req: ResearchRequest):
    if not req.company.strip():
        raise HTTPException(status_code=400, detail="Company name is required")
    try:
        bundle = _search.search_company(req.company.strip())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    try:
        analysis = synthesize(bundle, _llm)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "bundle": bundle.model_dump(mode="json"),
        "analysis": analysis,
    }


# ── Serve the built frontend (production / Docker) ──────────────────────────────
# Registered after the /api routes so they keep priority. The catch-all returns
# index.html for client-side routes (e.g. /c/:slug) so deep links work.
if _STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=_STATIC_DIR / "assets"), name="assets")

    @app.get("/")
    def _index():
        return FileResponse(_STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    def _spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = _STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_STATIC_DIR / "index.html")
