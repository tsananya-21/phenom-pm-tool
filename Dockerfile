# ── Stage 1: build the React frontend ──────────────────────────────────────────
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: backend + serve the built frontend ────────────────────────────────
FROM python:3.11-slim

# Hugging Face Spaces run the container as uid 1000.
RUN useradd -m -u 1000 user
WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
# Built frontend goes where api.py expects it (backend/static).
COPY --from=frontend /app/frontend/dist ./backend/static

RUN chown -R user:user /app
USER user

ENV HOME=/home/user \
    PHENOM_LLM_PROVIDER=anthropic \
    PHENOM_SEARCH_PROVIDER=tavily

# HF Spaces expect the app on port 7860.
EXPOSE 7860
CMD ["uvicorn", "api:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "7860"]
