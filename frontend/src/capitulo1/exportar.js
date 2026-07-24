// Compila la captura completa en texto plano, para analizarla directamente en
// una conversación con Claude cuando el canal integrado no esté disponible.

const PROMPT_CABECERA = `Actúa como el agente de análisis del Capítulo 1 (Propósito del consejo) de la
metodología «Arquitectura de Consejo». Ponderas y propones; el consultor
califica y decide, así que tu dictamen es PRELIMINAR. Las observaciones del
consultor pesan tanto como las respuestas.

Emite: (1) tres semáforos —«Gobierno vs. validación» (P1 vs P4), «Permeabilidad
al consejo ajeno» (P6) y «Coherencia de expectativa» (P8 vs P10)— cada uno en
rojo/amarillo/verde con fundamento; (2) jerarquía de propósitos (dominante + 2
secundarios) fundada en las respuestas; (3) puntos para la sesión de devolución;
(4) borrador de declaración de propósito (una cuartilla); y (5) recomendación
final: proceder / proceder con reservas / esperar.

--- ENTREVISTA ---`;

export function compilarTexto({ bloques, propositos, meta, respuestas, orden }) {
  const lineas = [PROMPT_CABECERA, ""];

  const metaLineas = [];
  if (meta.entrevistado) metaLineas.push(`Entrevistado: ${meta.entrevistado}`);
  if (meta.cargo) metaLineas.push(`Cargo/relación: ${meta.cargo}`);
  if (meta.empresa) metaLineas.push(`Empresa: ${meta.empresa}`);
  if (meta.fecha) metaLineas.push(`Fecha: ${meta.fecha}`);
  if (metaLineas.length) {
    lineas.push("DATOS DE LA ENTREVISTA", ...metaLineas, "");
  }

  const propNombre = Object.fromEntries(propositos.map((p) => [p.id, p.nombre]));

  for (const bloque of bloques) {
    lineas.push(`${bloque.titulo} (${bloque.subtitulo})`);
    for (const pregunta of bloque.preguntas) {
      if (pregunta.tipo === "orden_propositos") {
        lineas.push(`\nP${pregunta.id}. ${pregunta.texto}`);
        if (orden.length) {
          orden.forEach((id, i) => {
            lineas.push(`  ${i + 1}º — ${propNombre[id] || id}`);
          });
        } else {
          lineas.push("  (sin orden capturado)");
        }
        continue;
      }
      const r = respuestas[pregunta.id] || {};
      lineas.push(`\nP${pregunta.id}. ${pregunta.texto}`);
      lineas.push(`Respuesta: ${(r.respuesta || "").trim() || "(sin respuesta)"}`);
      if ((r.observaciones || "").trim()) {
        lineas.push(`Observaciones del consultor: ${r.observaciones.trim()}`);
      }
    }
    lineas.push("");
  }

  return lineas.join("\n").trim() + "\n";
}
