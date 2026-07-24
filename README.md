# Reclaude — Metodología de consejo (LLM Council)

Una app web donde un **consejo de modelos Claude** delibera sobre tu pregunta:
cada miembro responde por su cuenta, después se evalúan entre sí de forma
anónima, y un modelo **presidente (chairman)** sintetiza la respuesta final.

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

## Archivos adjuntos

Puedes **adjuntar archivos** a tu consulta y el consejo los tendrá en cuenta:
tanto los miembros (etapa 1) como el chairman (etapa 3) los reciben como
bloques de contenido nativos de la API de Anthropic. Tipos admitidos:

- **Imágenes** (`image/png`, `image/jpeg`, `image/gif`, `image/webp`).
- **PDF** (`application/pdf`).
- **Texto y código** (`text/*`, JSON, etc.): se envían como documento de texto.

Los límites (tamaño por archivo, tamaño total y número de archivos) se
configuran en `backend/app/config.py`. Los archivos inválidos o que exceden los
límites se descartan con elegancia y la interfaz muestra un aviso.

## Arquitectura

```
backend/   FastAPI + SDK oficial `anthropic` (async)
  app/config.py    Composición del consejo (miembros + chairman)
  app/council.py   Lógica de las 3 etapas
  app/main.py      Endpoint SSE /api/council + servir el frontend
frontend/  React + Vite (SPA que consume el stream SSE)
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
Si envías adjuntos que se descartan, también recibirás un evento `attachments`
con los avisos.

Para adjuntar archivos, añade un array `attachments` con `filename`,
`media_type` y `data` (contenido en base64):

```bash
curl -N -X POST localhost:8000/api/council \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Resume este documento",
    "attachments": [
      {"filename": "notas.txt", "media_type": "text/plain",
       "data": "'$(base64 -w0 notas.txt)'"}
    ]
  }'
```

## Personalización

- **Composición del consejo:** edita `COUNCIL_MEMBERS` y `CHAIRMAN_MODEL` en
  `backend/app/config.py`.
- **Límites de tokens por etapa:** `ANSWER_MAX_TOKENS`, `REVIEW_MAX_TOKENS`,
  `CHAIRMAN_MAX_TOKENS` en el mismo archivo.
- **Límites de adjuntos:** `MAX_ATTACHMENT_BYTES`, `MAX_TOTAL_ATTACHMENT_BYTES`
  y `MAX_ATTACHMENTS` en el mismo archivo.
- **Prompts:** los system prompts de cada etapa están en `backend/app/council.py`.

## Notas

- Si un miembro falla (p. ej. rate limit), el error se captura por miembro y el
  consejo continúa con el resto; el fallo se muestra en la interfaz.
- Las llamadas usan *adaptive thinking* y la evaluación por pares usa **salida
  estructurada** para parsear el ranking de forma fiable.
