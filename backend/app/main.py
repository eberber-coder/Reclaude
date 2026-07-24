"""App FastAPI: endpoint SSE del consejo + servir el build del frontend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import capitulo1
from .council import run_council
from .models import Capitulo1Request, CouncilRequest, Dictamen

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


# --- Instrumento digital del Capítulo 1 (propósito del consejo) ---
@app.get("/api/capitulo1/cuestionario")
async def capitulo1_cuestionario() -> dict:
    """Estructura del cuestionario (bloques, preguntas) y los seis propósitos."""
    return capitulo1.cuestionario_publico()


@app.post("/api/capitulo1/analizar")
async def capitulo1_analizar(request: Capitulo1Request) -> Dictamen:
    """Genera el dictamen preliminar del agente a partir de la captura.

    El botón «Generar análisis» del frontend se activa con al menos seis
    respuestas y el orden de propósitos completo; el backend valida lo mismo.
    """
    respondidas = sum(1 for r in request.respuestas if r.respuesta.strip())
    if respondidas < 6:
        raise HTTPException(
            status_code=422,
            detail="Se requieren al menos seis respuestas para generar el análisis.",
        )
    if len(request.orden_propositos) < 3:
        raise HTTPException(
            status_code=422,
            detail="Ordena los tres propósitos principales (pregunta 10) antes de analizar.",
        )
    try:
        return await capitulo1.generar_dictamen(request)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"{type(exc).__name__}: {exc}"
        ) from exc


# --- Servir el frontend construido (frontend/dist), si existe ---
# Repo root = backend/app/main.py -> parents[2]
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="frontend")
