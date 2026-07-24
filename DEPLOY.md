# Poner la aplicación en línea (con el agente integrado)

Esta guía deja la app corriendo en internet, con una URL `https://…` que puedes
abrir desde Safari en el iPhone, iPad o Mac. A diferencia del artefacto de
captura, aquí el botón **«Generar análisis del agente»** funciona de principio a
fin dentro de la app.

> El agente necesita un servidor y una **clave de API de Anthropic**. Por eso el
> despliegue lo activas tú (con tu cuenta y tu clave); no puede hacerlo nadie por
> ti. Los pasos están pensados para hacerse sin ser programador, en ~10 minutos.

---

## Paso 0 — Consigue tu clave de API de Anthropic

1. Entra a **https://console.anthropic.com** e inicia sesión.
2. Ve a **API Keys → Create Key**, ponle un nombre (p. ej. «Arquitectura de
   Consejo») y **copia la clave** (empieza por `sk-ant-…`). Guárdala; no se vuelve
   a mostrar.
3. Necesitarás algo de saldo/crédito en la cuenta para que las llamadas
   funcionen.

> La clave es como una contraseña: no la compartas ni la escribas dentro del
> código. Solo se pega en el panel del hosting (Paso 2).

---

## Opción recomendada — Render (tiene nivel gratuito)

Render conecta tu repositorio de GitHub y construye la app sola gracias al
`Dockerfile` y al `render.yaml` que ya están en el proyecto.

1. Entra a **https://render.com** y regístrate (puedes usar tu cuenta de GitHub).
2. **New +** → **Blueprint**.
3. Conecta el repositorio **`eberber-coder/Reclaude`** y elige la rama
   **`claude/new-session-o5q4jv`**. Render detectará `render.yaml` y propondrá un
   servicio web llamado `reclaude`. Pulsa **Apply**.
4. Cuando pregunte por la variable **`ANTHROPIC_API_KEY`**, pega tu clave del
   Paso 0. (Si no la pide durante la creación: entra al servicio → **Environment**
   → **Add Environment Variable**, clave `ANTHROPIC_API_KEY`, valor tu `sk-ant-…`,
   y guarda.)
5. Render construye y despliega (unos minutos la primera vez). Al terminar verás
   una URL del tipo **`https://reclaude.onrender.com`**.
6. Ábrela en Safari y, arriba, elige **«Capítulo 1 · Propósito»**.

**Sobre el nivel gratuito:** el servicio «se duerme» tras un rato sin uso, así
que la primera visita después de una pausa puede tardar ~1 minuto en despertar.
Para dejarlo siempre activo, sube el plan del servicio a **Starter** (de pago) en
**Settings → Instance Type**.

### Guardarlo a mano en el iPhone/iPad
En Safari, con la URL abierta: **Compartir → «Agregar a pantalla de inicio»**.
Queda como si fuera una app.

---

## Alternativas (misma imagen Docker)

El mismo `Dockerfile` funciona en otros servicios, por si prefieres uno:

- **Railway** (`https://railway.app`): New Project → Deploy from GitHub repo →
  elige el repo. En **Variables**, añade `ANTHROPIC_API_KEY`. Railway detecta el
  `Dockerfile` solo. (Sin nivel gratuito permanente; suele costar ~5 USD/mes.)
- **Fly.io** (`https://fly.io`, requiere su herramienta de línea de comandos):
  `fly launch` (detecta el `Dockerfile`) y luego
  `fly secrets set ANTHROPIC_API_KEY=sk-ant-…`.
- **Google Cloud Run**: `gcloud run deploy` desde la carpeta del repo, con la
  variable de entorno `ANTHROPIC_API_KEY`.

---

## Probarlo en tu propia computadora (opcional)

Si tienes **Docker** instalado:

```bash
docker build -t reclaude .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-ant-… reclaude
# abre http://localhost:8000
```

Sin Docker, con Python y Node instalados, están los pasos manuales en el
`README.md` (sección «Puesta en marcha»).

---

## Qué NO hacer

- No pongas la clave `sk-ant-…` dentro de ningún archivo del repositorio ni en
  un commit. Va únicamente en las variables de entorno del hosting.
- No compartas la URL con la clave incrustada (nunca lo está: la clave vive solo
  en el servidor).
