# Imagen única que construye el frontend y sirve todo desde el backend.
# Portable a Render, Railway, Fly.io, Google Cloud Run, etc.

# --- Etapa 1: construir la SPA de React ---
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Etapa 2: backend (FastAPI) que sirve la API y el build ---
FROM python:3.12-slim
WORKDIR /app/backend

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
# El backend monta frontend/dist relativo a la raíz del repo (parents[2]).
COPY --from=frontend /app/frontend/dist /app/frontend/dist

ENV PORT=8000
EXPOSE 8000

# La clave se inyecta como variable de entorno ANTHROPIC_API_KEY en el hosting.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
