"""Lógica de la metodología de consejo (LLM council) en tres etapas.

1. Respuestas individuales — cada miembro responde en paralelo.
2. Evaluación por pares anónima — cada miembro rankea todas las respuestas
   (etiquetadas A/B/C..., mezcladas) mediante salida estructurada.
3. Síntesis del chairman — un modelo presidente redacta la respuesta final
   en streaming a partir de todas las respuestas y rankings.

`run_council` es un generador asíncrono que emite eventos a medida que avanza
cada etapa, para que la interfaz pueda mostrar el progreso en tiempo real.
"""

from __future__ import annotations

import asyncio
import random
import string
from typing import Any, AsyncGenerator

import anthropic

from . import config
from .attachments import build_blocks
from .models import Attachment, Ranking

# Un único cliente asíncrono; todos los modelos Claude comparten ANTHROPIC_API_KEY,
# que el SDK resuelve automáticamente desde el entorno.
_client = anthropic.AsyncAnthropic()


def _extract_text(message: anthropic.types.Message) -> str:
    """Concatena los bloques de texto de una respuesta (ignora los de thinking)."""
    return "".join(block.text for block in message.content if block.type == "text").strip()


def _user_content(query: str, attachment_blocks: list[dict[str, Any]]) -> Any:
    """Construye el contenido del mensaje de usuario.

    Si hay adjuntos, se colocan antes del texto (recomendación de la API) y se
    devuelve una lista de bloques; si no, basta con la cadena de la pregunta.
    """
    if not attachment_blocks:
        return query
    return [*attachment_blocks, {"type": "text", "text": query}]


# --------------------------------------------------------------------------- #
# Etapa 1: respuestas individuales
# --------------------------------------------------------------------------- #
async def _member_answer(model: str, content: Any) -> dict[str, Any]:
    """Pide a un miembro su respuesta independiente a la consulta."""
    try:
        message = await _client.messages.create(
            model=model,
            max_tokens=config.ANSWER_MAX_TOKENS,
            thinking={"type": "adaptive"},
            system=(
                "Eres un miembro de un consejo de expertos. Responde a la pregunta "
                "del usuario de la forma más precisa, útil y bien razonada posible. "
                "Si se adjuntan archivos, analízalos y básate en su contenido. "
                "Responde en el mismo idioma que la pregunta."
            ),
            messages=[{"role": "user", "content": content}],
        )
        return {
            "model": model,
            "display_name": config.display_name(model),
            "answer": _extract_text(message),
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001 — degradar con elegancia por miembro
        return {
            "model": model,
            "display_name": config.display_name(model),
            "answer": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


# --------------------------------------------------------------------------- #
# Etapa 2: evaluación por pares anónima
# --------------------------------------------------------------------------- #
def _anonymize(answers: list[dict[str, Any]]) -> tuple[str, dict[str, str]]:
    """Construye un bloque anónimo mezclado y el mapeo etiqueta -> modelo.

    Solo se anonimizan las respuestas sin error. Las etiquetas son A, B, C, ...
    """
    valid = [a for a in answers if not a["error"] and a["answer"]]
    shuffled = valid[:]
    random.shuffle(shuffled)

    labels = list(string.ascii_uppercase)
    label_to_model: dict[str, str] = {}
    blocks: list[str] = []
    for label, ans in zip(labels, shuffled):
        label_to_model[label] = ans["model"]
        blocks.append(f"### Respuesta {label}\n{ans['answer']}")

    return "\n\n".join(blocks), label_to_model


async def _member_review(
    model: str,
    query: str,
    anonymized_block: str,
    label_to_model: dict[str, str],
) -> dict[str, Any]:
    """Pide a un miembro que rankee las respuestas anónimas (salida estructurada)."""
    valid_labels = list(label_to_model.keys())
    try:
        message = await _client.messages.parse(
            model=model,
            max_tokens=config.REVIEW_MAX_TOKENS,
            system=(
                "Eres un evaluador imparcial de un consejo de expertos. Se te "
                "muestran varias respuestas anónimas a una misma pregunta. "
                "Ordénalas de mejor a peor según su precisión, rigor y utilidad. "
                "No sabes qué respuesta es tuya; sé objetivo."
            ),
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Pregunta original:\n{query}\n\n"
                        f"Respuestas a evaluar:\n{anonymized_block}\n\n"
                        f"Rankea usando exactamente estas etiquetas: "
                        f"{', '.join(valid_labels)}."
                    ),
                }
            ],
            output_format=Ranking,
        )
        parsed: Ranking | None = message.parsed_output
        if parsed is None:
            raise ValueError("no se pudo parsear el ranking")

        # Traducir etiquetas anónimas -> IDs de modelo reales (ignorar inválidas).
        ranked_models = [
            label_to_model[label]
            for label in parsed.ranking
            if label in label_to_model
        ]
        return {
            "model": model,
            "display_name": config.display_name(model),
            "ranked_models": ranked_models,
            "rationale": parsed.rationale,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "model": model,
            "display_name": config.display_name(model),
            "ranked_models": [],
            "rationale": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _consensus(rankings: list[dict[str, Any]], members: list[str]) -> list[dict[str, Any]]:
    """Agrega los rankings en una puntuación de consenso (menor = mejor posición media).

    A cada modelo se le suma su posición (0-indexada) en cada ranking donde aparece.
    Devuelve la lista ordenada por puntuación media ascendente.
    """
    points: dict[str, list[int]] = {m: [] for m in members}
    for r in rankings:
        for position, model in enumerate(r["ranked_models"]):
            if model in points:
                points[model].append(position)

    scored = []
    for model, positions in points.items():
        avg = sum(positions) / len(positions) if positions else float("inf")
        scored.append(
            {
                "model": model,
                "display_name": config.display_name(model),
                "average_position": None if avg == float("inf") else round(avg, 2),
                "votes": len(positions),
            }
        )
    scored.sort(key=lambda s: (s["average_position"] is None, s["average_position"] or 0))
    return scored


# --------------------------------------------------------------------------- #
# Etapa 3: síntesis del chairman (streaming)
# --------------------------------------------------------------------------- #
def _build_chairman_context(
    query: str,
    answers: list[dict[str, Any]],
    rankings: list[dict[str, Any]],
) -> str:
    parts = [f"Pregunta del usuario:\n{query}\n"]
    parts.append("Respuestas de los miembros del consejo:")
    for a in answers:
        if a["error"]:
            parts.append(f"- {a['display_name']}: (error: {a['error']})")
        else:
            parts.append(f"\n#### {a['display_name']}\n{a['answer']}")

    parts.append("\nEvaluaciones por pares (rankings):")
    for r in rankings:
        if r["error"]:
            parts.append(f"- {r['display_name']}: (error: {r['error']})")
        else:
            order = " > ".join(config.display_name(m) for m in r["ranked_models"])
            parts.append(f"- {r['display_name']} ordenó: {order}. Motivo: {r['rationale']}")

    return "\n".join(parts)


async def _chairman_stream(
    query: str,
    answers: list[dict[str, Any]],
    rankings: list[dict[str, Any]],
    attachment_blocks: list[dict[str, Any]],
) -> AsyncGenerator[str, None]:
    context = _build_chairman_context(query, answers, rankings)
    async with _client.messages.stream(
        model=config.CHAIRMAN_MODEL,
        max_tokens=config.CHAIRMAN_MAX_TOKENS,
        thinking={"type": "adaptive"},
        system=(
            "Eres el presidente (chairman) de un consejo de expertos. Has recibido "
            "las respuestas independientes de varios miembros y sus evaluaciones "
            "mutuas. Tu tarea es sintetizar una ÚNICA respuesta final, la mejor "
            "posible: integra lo más sólido de cada aportación, corrige errores o "
            "contradicciones, y resuelve los desacuerdos con criterio. No te limites "
            "a elegir una respuesta; combínalas en algo superior. Si se adjuntan "
            "archivos, tenlos en cuenta al elaborar la respuesta. Responde en el "
            "mismo idioma que la pregunta y no menciones el proceso interno del "
            "consejo salvo que sea relevante."
        ),
        messages=[{"role": "user", "content": _user_content(context, attachment_blocks)}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


# --------------------------------------------------------------------------- #
# Orquestador
# --------------------------------------------------------------------------- #
async def run_council(
    query: str,
    attachments: list[Attachment] | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Ejecuta las tres etapas y emite eventos de progreso."""
    members = config.COUNCIL_MEMBERS

    # Preparar los adjuntos como bloques de contenido (una sola vez) y avisar de
    # los que se hayan descartado.
    attachment_blocks, warnings = build_blocks(attachments or [])
    if warnings:
        yield {"event": "attachments", "data": {"warnings": warnings}}
    content = _user_content(query, attachment_blocks)

    # Etapa 1 — respuestas en paralelo.
    answers = await asyncio.gather(*(_member_answer(m, content) for m in members))
    answers = list(answers)
    yield {"event": "members", "data": {"answers": answers}}

    # Etapa 2 — evaluación por pares anónima.
    anonymized_block, label_to_model = _anonymize(answers)
    if label_to_model:
        rankings = await asyncio.gather(
            *(_member_review(m, query, anonymized_block, label_to_model) for m in members)
        )
        rankings = list(rankings)
    else:
        rankings = []
    consensus = _consensus(rankings, members)
    yield {"event": "rankings", "data": {"rankings": rankings, "consensus": consensus}}

    # Etapa 3 — síntesis del chairman en streaming.
    try:
        async for delta in _chairman_stream(query, answers, rankings, attachment_blocks):
            yield {"event": "final_delta", "data": {"text": delta}}
    except Exception as exc:  # noqa: BLE001
        yield {"event": "error", "data": {"message": f"{type(exc).__name__}: {exc}"}}

    yield {"event": "done", "data": {"chairman": config.display_name(config.CHAIRMAN_MODEL)}}
