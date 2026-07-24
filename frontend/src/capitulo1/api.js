// Cliente del instrumento digital del Capítulo 1.

export async function fetchCuestionario(signal) {
  const res = await fetch("/api/capitulo1/cuestionario", { signal });
  if (!res.ok) throw new Error(`No se pudo cargar el cuestionario (${res.status}).`);
  return res.json();
}

export async function analizar(captura, signal) {
  const res = await fetch("/api/capitulo1/analizar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(captura),
    signal,
  });
  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail = body.detail || "";
    } catch {
      detail = await res.text().catch(() => "");
    }
    throw new Error(detail || `Error del servidor (${res.status}).`);
  }
  return res.json();
}
