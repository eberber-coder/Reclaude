# Reclaude — Arquitectura de Consejo

App web con dos herramientas, seleccionables desde la navegación superior:

1. **Consejo de LLMs** — un consejo de modelos Claude delibera sobre tu
   pregunta: cada miembro responde por su cuenta, después se evalúan entre sí de
   forma anónima, y un modelo **presidente (chairman)** sintetiza la respuesta
   final.
2. **Capítulo 1 · Propósito** — el instrumento digital del Capítulo 1 de la
   metodología «Arquitectura de Consejo»: captura el cuestionario de propósito y
   un agente produce un **dictamen preliminar**. Principio rector: *el agente
   pondera y propone; el consultor califica y decide.*

## Cómo funciona el consejo

La consulta pasa por tres etapas:

1. **Respuestas individuales** — la pregunta se envía en paralelo a todos los
   miembros del consejo. Cada uno responde de forma independiente.
2. **Evaluación por pares (anónima)** — se recopilan las respuestas, se
   anonimizan (etiquetadas *Respuesta A / B / C…* y mezcladas para que ningún
   modelo sepa cuál es la suya) y cada miembro las ordena de mejor a peor con una
   justificación. Se agregan los votos en una **puntuación de consenso**.
3. **Síntesis del chairman** — un modelo presidente recibe la pregunta, todas
   las respuestas y todos los rankings, y redacta la respuesta final integrando
   lo mejor de cada aportación. Se transmite en *streaming*.

Todo el progreso se emite al navegador mediante **Server-Sent Events (SSE)**,
de modo que ves cada etapa en tiempo real.

## Cómo funciona el Capítulo 1 (propósito del consejo)

El instrumento acompaña la entrevista de propósito al propietario:

1. **Captura** — datos del entrevistado y la empresa; diez preguntas en tres
   bloques (situación, disposición, expectativa). Cada pregunta (1–9) tiene un
   campo de respuesta y un campo de **observaciones del consultor** (titubeos,
   molestias, contexto), que el agente pondera con el mismo peso que el texto.
   La pregunta 10 ordena tres de los seis propósitos con tarjetas (1º, 2º, 3º).
2. **Análisis** — el botón «Generar análisis del agente» se activa con al menos
   seis respuestas y el orden de propósitos completo.
3. **Dictamen** — el agente devuelve, siempre rotulado como *preliminar, sujeto
   al juicio del consultor*: tres **semáforos** (gobierno vs. validación,
   permeabilidad al consejo ajeno, coherencia de expectativa), la **jerarquía de
   propósitos** (dominante + dos secundarios) fundada en las respuestas, los
   **puntos para la sesión de devolución**, un **borrador de declaración de
   propósito** y la **recomendación final** (proceder / proceder con reservas /
   esperar).
4. **Alternativa** — «Exportar para analizar en Claude» compila toda la captura
   en texto (con el prompt del agente) para pegarla en una conversación con
   Claude cuando el canal integrado no esté disponible.

## Arquitectura

```
backend/   FastAPI + SDK oficial `anthropic` (async)
  app/config.py      Composición del consejo + modelo del agente del Cap. 1
  app/council.py     Lógica de las 3 etapas del consejo de LLMs
  app/capitulo1.py   Cuestionario de propósito + agente del dictamen preliminar
  app/models.py      Esquemas Pydantic (consejo y Capítulo 1)
  app/main.py        Endpoints SSE /api/council, /api/capitulo1/* + frontend
frontend/  React + Vite (SPA)
  src/components/     Vista del consejo de LLMs (SSE)
  src/capitulo1/      Vista del Capítulo 1 (captura, dictamen, exportación)
```

Todos los miembros son modelos de Claude, así que basta una única
`ANTHROPIC_API_KEY`. La composición por defecto (editable en
`backend/app/config.py`):

| Rol      | Modelo             |
| -------- | ------------------ |
| Miembro  | `claude-opus-4-8`  |
| Miembro  | `claude-sonnet-5`  |
| Miembro  | `claude-haiku-4-5` |
| Chairman | `claude-opus-4-8`  |

## Requisitos

- Python 3.11+
- Node.js 18+
- Una clave de API de Anthropic (`ANTHROPIC_API_KEY`)

## Puesta en marcha

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # y pon tu ANTHROPIC_API_KEY dentro
uvicorn app.main:app --reload
```

El backend queda en `http://localhost:8000`.

### 2. Frontend (desarrollo)

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite sirve la app en `http://localhost:5173` y redirige `/api` al backend.

### Despliegue en un solo proceso

Construye el frontend y sírvelo directamente desde el backend:

```bash
cd frontend && npm run build      # genera frontend/dist
cd ../backend && uvicorn app.main:app
```

FastAPI servirá la SPA en `http://localhost:8000/` (monta `frontend/dist` si
existe) y el endpoint del consejo en `/api/council`.

## Probar el endpoint directamente

```bash
curl -N -X POST localhost:8000/api/council \
  -H 'Content-Type: application/json' \
  -d '{"query": "¿Cuál es la mejor estrategia para aprender un idioma?"}'
```

Verás llegar los eventos SSE `members`, `rankings`, `final_delta` y `done`.

El instrumento del Capítulo 1 expone dos endpoints: `GET
/api/capitulo1/cuestionario` (bloques, preguntas y los seis propósitos) y `POST
/api/capitulo1/analizar` (recibe la captura y devuelve el dictamen estructurado).

## Personalización

- **Composición del consejo:** edita `COUNCIL_MEMBERS` y `CHAIRMAN_MODEL` en
  `backend/app/config.py`.
- **Límites de tokens por etapa:** `ANSWER_MAX_TOKENS`, `REVIEW_MAX_TOKENS`,
  `CHAIRMAN_MAX_TOKENS` en el mismo archivo.
- **Prompts:** los system prompts de cada etapa están en `backend/app/council.py`.
- **Agente del Capítulo 1:** modelo y tokens en `CAPITULO1_MODEL` /
  `CAPITULO1_MAX_TOKENS` (`config.py`); el cuestionario, los propósitos y las
  reglas de ponderación del agente están en `backend/app/capitulo1.py`.

## Notas

- Si un miembro falla (p. ej. rate limit), el error se captura por miembro y el
  consejo continúa con el resto; el fallo se muestra en la interfaz.
- Las llamadas usan *adaptive thinking* y la evaluación por pares usa **salida
  estructurada** para parsear el ranking de forma fiable.
