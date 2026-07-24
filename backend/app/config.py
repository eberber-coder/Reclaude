"""Configuración del consejo de LLMs.

Todos los miembros son modelos de Claude, así que comparten una única
`ANTHROPIC_API_KEY` (resuelta automáticamente por el SDK desde el entorno).
Edita estas listas para cambiar la composición del consejo.
"""

# Miembros del consejo: cada uno responde de forma independiente y luego
# evalúa (de forma anónima) las respuestas de los demás.
COUNCIL_MEMBERS: list[str] = [
    "claude-opus-4-8",
]

# Modelo "presidente" que sintetiza la respuesta final a partir de todas las
# respuestas y rankings del consejo.
CHAIRMAN_MODEL: str = "claude-fable-5"

# Nombres legibles para mostrar en la interfaz.
MODEL_DISPLAY_NAMES: dict[str, str] = {
    "claude-fable-5": "Claude Fable 5",
    "claude-opus-4-8": "Claude Opus 4.8",
    "claude-opus-4-7": "Claude Opus 4.7",
    "claude-sonnet-5": "Claude Sonnet 5",
    "claude-haiku-4-5": "Claude Haiku 4.5",
}


def display_name(model_id: str) -> str:
    """Devuelve un nombre legible para un ID de modelo."""
    return MODEL_DISPLAY_NAMES.get(model_id, model_id)


# --- Límites de tokens por etapa ---
ANSWER_MAX_TOKENS = 4096      # respuesta individual de cada miembro
REVIEW_MAX_TOKENS = 2048      # evaluación estructurada (ranking)
CHAIRMAN_MAX_TOKENS = 16000   # síntesis final (en streaming)

# --- Límites de archivos adjuntos ---
MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024        # tamaño máximo por archivo (8 MB)
MAX_TOTAL_ATTACHMENT_BYTES = 24 * 1024 * 1024  # tamaño máximo del conjunto (24 MB)
MAX_ATTACHMENTS = 10                            # nº máximo de archivos por consulta
