"""App FastAPI: endpoint SSE del consejo + servir el build del frontend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from .council import run_council
from .models import CouncilRequest

# Carga ANTHROPIC_API_KEY desde backend/.env si existe.
load_dotenv()

app = FastAPI(title="Reclaude — Consejo de LLMs")


def _sse(event: str, data: dict) -> str:
    """Formatea un evento como Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/council")
async def council(request: CouncilRequest) -> StreamingResponse:
    """Ejecuta el consejo y emite el progreso como stream SSE."""

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for message in run_council(request.query):
                yield _sse(message["event"], message["data"])
        except Exception as exc:  # noqa: BLE001
            yield _sse("error", {"message": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


# --- Servir el frontend construido (frontend/dist), si existe ---
# Repo root = backend/app/main.py -> parents[2]
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="frontend")
