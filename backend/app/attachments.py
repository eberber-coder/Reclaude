"""Conversión de archivos adjuntos a bloques de contenido de la API de Anthropic.

Cada :class:`~.models.Attachment` (bytes en base64 + tipo MIME) se traduce al
bloque de contenido adecuado para pasarlo a los modelos:

- ``image/*``          -> bloque ``image`` (base64).
- ``application/pdf``  -> bloque ``document`` (base64).
- ``text/*`` y demás   -> bloque ``document`` con fuente de texto (se decodifica
  el base64 a UTF-8). Cubre texto plano, markdown y código fuente.

Se aplican límites de tamaño (ver ``config``) y los archivos inválidos se
descartan con elegancia, devolviendo además avisos legibles para la interfaz.
"""

from __future__ import annotations

import base64
import binascii
from typing import Any

from . import config
from .models import Attachment

# Tipos de imagen que la API acepta como bloque `image`.
_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def _decode(data: str) -> bytes:
    """Decodifica base64 de forma estricta; lanza ValueError si es inválido."""
    try:
        return base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"base64 inválido: {exc}") from exc


def _text_document_block(text: str, filename: str) -> dict[str, Any]:
    """Bloque `document` con fuente de texto (para texto plano y código)."""
    return {
        "type": "document",
        "source": {"type": "text", "media_type": "text/plain", "data": text},
        "title": filename,
    }


def _one_block(att: Attachment) -> dict[str, Any]:
    """Convierte un adjunto en un bloque de contenido. Lanza ValueError si no es válido."""
    raw = _decode(att.data)
    if len(raw) > config.MAX_ATTACHMENT_BYTES:
        mb = config.MAX_ATTACHMENT_BYTES / (1024 * 1024)
        raise ValueError(f"supera el máximo por archivo ({mb:.0f} MB)")

    media_type = (att.media_type or "").lower().split(";", 1)[0].strip()

    if media_type in _IMAGE_TYPES:
        return {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": att.data},
        }

    if media_type == "application/pdf":
        return {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": att.data},
            "title": att.filename,
        }

    # Todo lo demás (text/*, application/json, código sin tipo, etc.) se trata
    # como texto: se intenta decodificar como UTF-8.
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"tipo no soportado ('{media_type or 'desconocido'}') y no es texto UTF-8"
        ) from exc
    return _text_document_block(text, att.filename)


def build_blocks(attachments: list[Attachment]) -> tuple[list[dict[str, Any]], list[str]]:
    """Convierte los adjuntos en bloques de contenido y recopila avisos.

    Devuelve ``(bloques, avisos)``. Los archivos inválidos o que exceden los
    límites se omiten y se añade un aviso legible por cada uno. También se
    aplican los límites globales de número y tamaño total.
    """
    blocks: list[dict[str, Any]] = []
    warnings: list[str] = []

    if len(attachments) > config.MAX_ATTACHMENTS:
        warnings.append(
            f"Solo se procesan los primeros {config.MAX_ATTACHMENTS} archivos "
            f"(se enviaron {len(attachments)})."
        )
        attachments = attachments[: config.MAX_ATTACHMENTS]

    total = 0
    for att in attachments:
        try:
            block = _one_block(att)
        except ValueError as exc:
            warnings.append(f"«{att.filename}» omitido: {exc}.")
            continue

        # Control del tamaño total acumulado (sobre los bytes originales).
        try:
            size = len(_decode(att.data))
        except ValueError:
            size = 0
        if total + size > config.MAX_TOTAL_ATTACHMENT_BYTES:
            mb = config.MAX_TOTAL_ATTACHMENT_BYTES / (1024 * 1024)
            warnings.append(
                f"«{att.filename}» omitido: se supera el tamaño total máximo ({mb:.0f} MB)."
            )
            continue
        total += size
        blocks.append(block)

    return blocks, warnings
