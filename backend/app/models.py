"""Esquemas Pydantic para la API y para las salidas estructuradas del consejo."""

from pydantic import BaseModel, Field


class CouncilRequest(BaseModel):
    """Petición entrante con la consulta del usuario."""

    query: str = Field(..., min_length=1, description="La pregunta para el consejo")


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


# --------------------------------------------------------------------------- #
# Instrumento digital del Capítulo 1 (propósito del consejo)
# --------------------------------------------------------------------------- #
class RespuestaCapturada(BaseModel):
    """Respuesta a una pregunta del cuestionario, con la observación conductual
    del consultor (titubeos, molestias, contexto), que el agente pondera con el
    mismo peso que el texto de la respuesta."""

    pregunta_id: int = Field(..., ge=1, le=9, description="Número de pregunta (1-9)")
    respuesta: str = Field("", description="Lo que respondió el entrevistado")
    observaciones: str = Field(
        "", description="Observaciones conductuales del consultor sobre la respuesta"
    )


class Capitulo1Request(BaseModel):
    """Captura completa de la entrevista de propósito (preguntas 1-9 con
    observaciones y el orden de los tres propósitos principales, pregunta 10)."""

    entrevistado: str = Field("", description="Nombre del entrevistado")
    cargo: str = Field("", description="Cargo o relación con la empresa")
    empresa: str = Field("", description="Nombre de la empresa")
    fecha: str = Field("", description="Fecha de la entrevista")
    respuestas: list[RespuestaCapturada] = Field(default_factory=list)
    orden_propositos: list[str] = Field(
        default_factory=list,
        description="IDs de los tres propósitos principales, ordenados 1º, 2º, 3º",
    )


# --- Salida estructurada del agente: el dictamen preliminar ---
class Semaforo(BaseModel):
    """Uno de los tres semáforos que produce el agente."""

    nombre: str = Field(..., description="Nombre del semáforo")
    color: str = Field(..., description="Uno de: rojo, amarillo, verde")
    fundamento: str = Field(..., description="Justificación breve del color, anclada a las respuestas")


class PropositoJerarquizado(BaseModel):
    """Un propósito dentro de la jerarquía propuesta, con su fundamento."""

    proposito: str = Field(..., description="Nombre del propósito")
    fundamento: str = Field(..., description="Por qué, según las respuestas (no la teoría)")


class Recomendacion(BaseModel):
    """Recomendación final del agente (siempre preliminar)."""

    decision: str = Field(
        ..., description="Uno de: proceder, proceder con reservas, esperar"
    )
    fundamento: str = Field(..., description="Justificación de la recomendación")


class Dictamen(BaseModel):
    """Dictamen preliminar del agente. Rotulado siempre como sujeto al juicio
    del consultor: el agente pondera y propone; el consultor califica y decide."""

    semaforos: list[Semaforo] = Field(
        ..., description="Los tres semáforos: gobierno vs. validación, permeabilidad, coherencia"
    )
    proposito_dominante: PropositoJerarquizado
    propositos_secundarios: list[PropositoJerarquizado] = Field(
        ..., description="Máximo dos propósitos secundarios"
    )
    puntos_devolucion: list[str] = Field(
        ..., description="Puntos para la sesión de devolución (contradicciones como hallazgos, no reproches)"
    )
    borrador_declaracion: str = Field(
        ..., description="Borrador de la declaración de propósito (una cuartilla)"
    )
    recomendacion: Recomendacion
