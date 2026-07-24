"""Instrumento digital del Capítulo 1: propósito del consejo.

Prototipo del agente que acompaña la captura del cuestionario de propósito.
Principio rector, visible en toda la aplicación: **el agente pondera y propone;
el consultor califica y decide**. La información conductual de la entrevista
—titubeos, molestias, contexto— se captura en las «observaciones del consultor»
por pregunta y el agente la pondera con el mismo peso que las respuestas.

Este módulo define, como fuente única de verdad:

* `CUESTIONARIO` — los tres bloques y sus diez preguntas (1.2 del documento);
* `PROPOSITOS` — los seis propósitos del consejo (Anexo A);
* `generar_dictamen` — la llamada al agente, que devuelve un `Dictamen`
  estructurado (semáforos, jerarquía de propósitos, puntos de devolución,
  borrador de declaración y recomendación).
"""

from __future__ import annotations

import anthropic

from . import config
from .models import Capitulo1Request, Dictamen

# Cliente compartido; el SDK resuelve ANTHROPIC_API_KEY desde el entorno.
_client = anthropic.AsyncAnthropic()


# --------------------------------------------------------------------------- #
# Cuestionario de propósito (fuente única de verdad para backend y frontend)
# --------------------------------------------------------------------------- #
# Cada pregunta de los bloques A–B–C (1 a 9) se captura con un campo de
# respuesta y un campo de observaciones del consultor. La pregunta 10 no es de
# texto: es el ordenamiento de tres propósitos mediante tarjetas.
CUESTIONARIO: list[dict] = [
    {
        "bloque": "A",
        "titulo": "Bloque A — La situación",
        "subtitulo": "revela la necesidad real",
        "preguntas": [
            {
                "id": 1,
                "texto": "¿Cuáles fueron las tres decisiones más importantes de los "
                "últimos dos años, y quién participó en cada una?",
            },
            {
                "id": 2,
                "texto": "¿Qué decisión reciente le habría gustado tomar de otra "
                "manera, y qué le faltó para hacerlo?",
            },
            {
                "id": 3,
                "texto": "Si usted faltara mañana durante seis meses, ¿qué decisiones "
                "se detendrían?",
            },
        ],
    },
    {
        "bloque": "B",
        "titulo": "Bloque B — La disposición",
        "subtitulo": "revela si hay proyecto o simulación",
        "preguntas": [
            {
                "id": 4,
                "texto": "Mencione una decisión concreta que hoy toma usted solo y que "
                "estaría dispuesto a someter a un consejo. ¿Y una que no cedería nunca?",
            },
            {
                "id": 5,
                "texto": "¿Qué haría si el consejo le recomendara, por unanimidad, algo "
                "contrario a su convicción?",
            },
            {
                "id": 6,
                "texto": "¿Ha tenido antes asesores o consejeros cuya opinión haya "
                "cambiado una decisión suya? Deme un ejemplo.",
            },
            {
                "id": 7,
                "texto": "¿Quién en su empresa o familia se opondría a la existencia de "
                "un consejo, y por qué?",
            },
        ],
    },
    {
        "bloque": "C",
        "titulo": "Bloque C — La expectativa",
        "subtitulo": "revela el propósito dominante",
        "preguntas": [
            {
                "id": 8,
                "texto": "Complete la frase: «Quiero un consejo porque necesito que "
                "alguien decida / vigile / aporte ______, que hoy nadie hace».",
            },
            {
                "id": 9,
                "texto": "¿Cómo sabría, dentro de tres años, que el consejo valió la "
                "pena? Descríbalo en resultados observables.",
            },
            {
                "id": 10,
                "texto": "De estos seis propósitos, ordene los tres principales.",
                "tipo": "orden_propositos",
            },
        ],
    },
]

# Los seis propósitos del consejo (Anexo A). El `id` es la clave estable que
# viaja en `orden_propositos`; `nombre` y `descripcion` son para mostrar.
PROPOSITOS: list[dict] = [
    {
        "id": "decisiones",
        "nombre": "Mejores decisiones",
        "descripcion": "Incorporar experiencia, perspectiva externa y debate "
        "estructurado a decisiones que hoy toma una sola persona.",
    },
    {
        "id": "contrapeso",
        "nombre": "Contrapeso institucional",
        "descripcion": "Someter el poder —incluso el del fundador— a un foro con "
        "reglas; el antídoto contra los puntos ciegos del éxito.",
    },
    {
        "id": "continuidad",
        "nombre": "Continuidad",
        "descripcion": "Institucionalizar la empresa para que sobreviva a las "
        "personas: sucesión, transición generacional, memoria institucional.",
    },
    {
        "id": "patrimonio",
        "nombre": "Protección patrimonial",
        "descripcion": "Vigilancia sobre la administración, partes relacionadas y "
        "riesgos que la operación diaria no ve o no quiere ver.",
    },
    {
        "id": "confianza",
        "nombre": "Confianza ante terceros",
        "descripcion": "Bancos, inversionistas y sucesores valoran una empresa "
        "gobernada; reduce el «descuento por persona clave».",
    },
    {
        "id": "separacion",
        "nombre": "Separación familia–empresa",
        "descripcion": "Dar a la familia un cauce como propietaria sin que gobierne "
        "desde la cocina; profesionaliza la relación familia–empresa.",
    },
]

_PROPOSITOS_POR_ID = {p["id"]: p for p in PROPOSITOS}
_PREGUNTAS_POR_ID = {
    pregunta["id"]: pregunta
    for bloque in CUESTIONARIO
    for pregunta in bloque["preguntas"]
}


def cuestionario_publico() -> dict:
    """Estructura del cuestionario y los propósitos para el frontend."""
    return {"bloques": CUESTIONARIO, "propositos": PROPOSITOS}


# --------------------------------------------------------------------------- #
# Reglas del agente (Parte III · «Reglas de ponderación del agente»)
# --------------------------------------------------------------------------- #
_SYSTEM_PROMPT = """\
Eres el agente de análisis del instrumento digital del Capítulo 1 (Propósito \
del consejo) de la metodología «Arquitectura de Consejo». Acompañas a un \
consultor de gobierno corporativo que acaba de entrevistar al propietario o \
accionista controlador de una empresa.

PRINCIPIO RECTOR, INNEGOCIABLE: tú ponderas y propones; el consultor califica y \
decide. Todo tu dictamen es PRELIMINAR y está sujeto al juicio del consultor. \
Nunca afirmes conclusiones como definitivas; propón, funda y señala lo que \
falta por contrastar.

Las «observaciones del consultor» de cada pregunta (titubeos, molestias, \
lenguaje corporal, contexto) pesan TANTO como el texto de la respuesta. \
Considéralas con el mismo rigor.

Debes producir EXACTAMENTE TRES SEMÁFOROS, en este orden, cada uno con color \
(rojo, amarillo o verde) y un fundamento breve anclado a las respuestas:

1. «Gobierno vs. validación» — contraste entre la P1 (qué decisiones importantes \
   y quién participó) y la P4 (qué cedería y qué no). Si concentra todas las \
   decisiones y cedería poco → ROJO (busca validación, no gobierno). Apertura \
   genuina con decisiones concretas que someterá → VERDE. Ambiguo → AMARILLO. \
   Refuerza con la P3 (qué se detendría sin él) y la P5 (qué haría ante una \
   recomendación unánime contraria).

2. «Permeabilidad al consejo ajeno» — se lee sobre la P6. Sin ejemplo concreto \
   de una decisión que haya cambiado por consejo ajeno → ROJO (quien nunca \
   cambió difícilmente empezará ahora). Ejemplo vago → AMARILLO. Ejemplo \
   concreto y verificable → VERDE.

3. «Coherencia de expectativa» — contraste entre la P8 (frase espontánea) y la \
   P10 (orden asistido de propósitos). Coinciden → VERDE. Divergencia parcial → \
   AMARILLO. Contradicción → ROJO. La divergencia NO es un error: es material \
   para la sesión de devolución.

JERARQUÍA DE PROPÓSITOS: propón un propósito dominante y como máximo dos \
secundarios, fundados en las respuestas (no en la teoría). Respeta el orden \
declarado por el propietario en la P10, pero señala en el fundamento si las \
respuestas apuntan a otro propósito (eso también es material de devolución). \
Los seis propósitos posibles son: Mejores decisiones, Contrapeso institucional, \
Continuidad, Protección patrimonial, Confianza ante terceros y \
Separación familia–empresa.

PUNTOS DE DEVOLUCIÓN: lista breve para la segunda reunión. Incluye las \
contradicciones detectadas presentadas como hallazgos (nunca como reproches), \
la prueba de consecuencia del propósito propuesto («si el propósito es X, el \
consejo tendrá Y desde el primer año; ¿está de acuerdo?») y las señales de \
éxito de la P9 que alimentarán el tablero de métricas.

BORRADOR DE DECLARACIÓN DE PROPÓSITO: una cuartilla con cinco campos —propósito \
dominante y secundarios; tres decisiones concretas que el propietario se \
compromete a someter al consejo desde el primer año; señales de éxito a tres \
años (de la P9); lo que el consejo NO será; y una nota de que se relee en la \
primera autoevaluación anual—. Redáctalo como borrador que el propietario \
peleará y hará suyo, no como texto cerrado.

RECOMENDACIÓN FINAL, uno de tres desenlaces (los tres son profesionales; \
aconsejar esperar no es un fracaso):
- «proceder» — hay propósito genuino y disposición; semáforos mayormente verdes.
- «proceder con reservas» — hay proyecto pero con señales amarillas que atender \
  en la devolución o antes de diseñar.
- «esperar» — un rojo en «Gobierno vs. validación» o en «Permeabilidad» suele \
  bastar: sin disposición real a ser contradicho, el consejo sería simulación. \
  Recomienda esperar y contrastar más adelante.

Responde SIEMPRE en español. Sé concreto, sobrio y honesto; evita la adulación \
y la venta. Un caso dudoso se nombra como dudoso.\
"""


def _serializar_captura(req: Capitulo1Request) -> str:
    """Compone el texto de la entrevista que recibe el agente."""
    lineas: list[str] = []
    encabezado = []
    if req.entrevistado:
        encabezado.append(f"Entrevistado: {req.entrevistado}")
    if req.cargo:
        encabezado.append(f"Cargo/relación: {req.cargo}")
    if req.empresa:
        encabezado.append(f"Empresa: {req.empresa}")
    if req.fecha:
        encabezado.append(f"Fecha: {req.fecha}")
    if encabezado:
        lineas.append("DATOS DE LA ENTREVISTA")
        lineas.extend(encabezado)
        lineas.append("")

    respuestas = {r.pregunta_id: r for r in req.respuestas}
    lineas.append("RESPUESTAS AL CUESTIONARIO (preguntas 1 a 9)")
    for pid in range(1, 10):
        pregunta = _PREGUNTAS_POR_ID.get(pid)
        if pregunta is None:
            continue
        lineas.append(f"\nP{pid}. {pregunta['texto']}")
        r = respuestas.get(pid)
        respuesta = (r.respuesta.strip() if r else "") or "(sin respuesta)"
        lineas.append(f"Respuesta: {respuesta}")
        observaciones = (r.observaciones.strip() if r else "")
        if observaciones:
            lineas.append(f"Observaciones del consultor: {observaciones}")

    lineas.append("\nP10. Orden de propósitos elegido por el propietario (asistido):")
    if req.orden_propositos:
        for i, pid in enumerate(req.orden_propositos, start=1):
            prop = _PROPOSITOS_POR_ID.get(pid)
            nombre = prop["nombre"] if prop else pid
            lineas.append(f"  {i}º — {nombre}")
    else:
        lineas.append("  (sin orden capturado)")

    return "\n".join(lineas)


async def generar_dictamen(req: Capitulo1Request) -> Dictamen:
    """Llama al agente y devuelve el dictamen preliminar estructurado."""
    captura = _serializar_captura(req)
    message = await _client.messages.parse(
        model=config.CAPITULO1_MODEL,
        max_tokens=config.CAPITULO1_MAX_TOKENS,
        thinking={"type": "adaptive"},
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Analiza la siguiente entrevista de propósito y emite tu "
                    "dictamen preliminar.\n\n" + captura
                ),
            }
        ],
        output_format=Dictamen,
    )
    dictamen = message.parsed_output
    if dictamen is None:
        raise ValueError("El agente no devolvió un dictamen parseable.")
    return dictamen
