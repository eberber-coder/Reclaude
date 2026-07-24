"""Esquemas Pydantic para la API y para las salidas estructuradas del consejo."""

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """Un archivo adjunto a la consulta (PDF, imagen o texto/código).

    `data` son los bytes del archivo codificados en base64 (sin el prefijo
    `data:`). `media_type` es el tipo MIME (p. ej. `application/pdf`,
    `image/png`, `text/plain`); el backend decide cómo convertirlo en un
    bloque de contenido de la API a partir de él.
    """

    filename: str = Field(..., description="Nombre del archivo, para mostrarlo y etiquetarlo")
    media_type: str = Field(
        default="application/octet-stream",
        description="Tipo MIME del archivo (image/*, application/pdf, text/*, ...)",
    )
    data: str = Field(..., description="Contenido del archivo codificado en base64")


class CouncilRequest(BaseModel):
    """Petición entrante con la consulta del usuario."""

    query: str = Field(..., min_length=1, description="La pregunta para el consejo")
    attachments: list[Attachment] = Field(
        default_factory=list,
        description="Archivos adjuntos que el consejo debe tener en cuenta",
    )


class Ranking(BaseModel):
    """Salida estructurada que produce cada miembro al evaluar a sus pares.

    `ranking` es la lista de etiquetas anónimas ("A", "B", "C", ...) ordenada
    de mejor a peor. `rationale` es una justificación breve del orden elegido.
    """

    ranking: list[str] = Field(
        ...,
        description="Etiquetas de respuesta ordenadas de mejor a peor (p. ej. ['B', 'A', 'C'])",
    )
    rationale: str = Field(
        ...,
        description="Justificación breve del ranking (2-4 frases)",
    )


class MemberAnswer(BaseModel):
    """Respuesta de un miembro en la etapa 1 (des-anonimizada para la UI)."""

    model: str
    display_name: str
    answer: str
    error: str | None = None


class MemberRanking(BaseModel):
    """Ranking emitido por un miembro en la etapa 2 (des-anonimizado)."""

    model: str
    display_name: str
    # Ranking traducido de etiquetas anónimas a IDs de modelo reales.
    ranked_models: list[str]
    rationale: str
    error: str | None = None
