import { useEffect, useMemo, useRef, useState } from "react";
import { fetchCuestionario, analizar } from "./api.js";
import { compilarTexto } from "./exportar.js";
import OrdenPropositos from "./OrdenPropositos.jsx";
import Dictamen from "./Dictamen.jsx";

// Instrumento digital del Capítulo 1: captura del cuestionario de propósito con
// agente que pondera y propone un dictamen preliminar; el consultor decide.
export default function Capitulo1() {
  const [cuestionario, setCuestionario] = useState(null);
  const [cargaError, setCargaError] = useState(null);

  const [meta, setMeta] = useState({
    entrevistado: "",
    cargo: "",
    empresa: "",
    fecha: "",
  });
  // respuestas[preguntaId] = { respuesta, observaciones }
  const [respuestas, setRespuestas] = useState({});
  const [orden, setOrden] = useState([]);

  const [analizando, setAnalizando] = useState(false);
  const [dictamen, setDictamen] = useState(null);
  const [error, setError] = useState(null);
  const [copiado, setCopiado] = useState(false);
  const abortRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchCuestionario(controller.signal)
      .then(setCuestionario)
      .catch((e) => {
        if (e.name !== "AbortError") setCargaError(e.message);
      });
    return () => controller.abort();
  }, []);

  const preguntasTexto = useMemo(() => {
    if (!cuestionario) return [];
    return cuestionario.bloques
      .flatMap((b) => b.preguntas)
      .filter((p) => p.tipo !== "orden_propositos");
  }, [cuestionario]);

  const respondidas = useMemo(
    () =>
      preguntasTexto.filter((p) => (respuestas[p.id]?.respuesta || "").trim())
        .length,
    [preguntasTexto, respuestas]
  );

  const listoParaAnalizar = respondidas >= 6 && orden.length >= 3;

  function setCampo(id, campo, valor) {
    setRespuestas((prev) => ({
      ...prev,
      [id]: { ...prev[id], [campo]: valor },
    }));
  }

  function payload() {
    return {
      ...meta,
      respuestas: preguntasTexto.map((p) => ({
        pregunta_id: p.id,
        respuesta: respuestas[p.id]?.respuesta || "",
        observaciones: respuestas[p.id]?.observaciones || "",
      })),
      orden_propositos: orden,
    };
  }

  async function generar() {
    if (!listoParaAnalizar || analizando) return;
    setAnalizando(true);
    setError(null);
    setDictamen(null);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const result = await analizar(payload(), controller.signal);
      setDictamen(result);
    } catch (e) {
      if (e.name !== "AbortError") setError(e.message);
    } finally {
      setAnalizando(false);
      abortRef.current = null;
    }
  }

  async function exportar() {
    const texto = compilarTexto({
      bloques: cuestionario.bloques,
      propositos: cuestionario.propositos,
      meta,
      respuestas,
      orden,
    });
    try {
      await navigator.clipboard.writeText(texto);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2500);
    } catch {
      // Si el portapapeles no está disponible, ofrecer descarga.
      const blob = new Blob([texto], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "entrevista-proposito.txt";
      a.click();
      URL.revokeObjectURL(url);
    }
  }

  if (cargaError) {
    return <div className="error-banner">⚠ {cargaError}</div>;
  }
  if (!cuestionario) {
    return <p className="subtitle">Cargando cuestionario…</p>;
  }

  return (
    <>
      <p className="subtitle">
        Captura del cuestionario de propósito. El agente pondera y propone; el
        consultor califica y decide.
      </p>

      {/* Datos del entrevistado y empresa */}
      <div className="stage">
        <h2>Datos de la entrevista</h2>
        <div className="meta-grid">
          <label>
            Entrevistado
            <input
              value={meta.entrevistado}
              onChange={(e) => setMeta({ ...meta, entrevistado: e.target.value })}
              placeholder="Nombre"
            />
          </label>
          <label>
            Cargo / relación
            <input
              value={meta.cargo}
              onChange={(e) => setMeta({ ...meta, cargo: e.target.value })}
              placeholder="Propietario, accionista controlador…"
            />
          </label>
          <label>
            Empresa
            <input
              value={meta.empresa}
              onChange={(e) => setMeta({ ...meta, empresa: e.target.value })}
              placeholder="Razón social"
            />
          </label>
          <label>
            Fecha
            <input
              value={meta.fecha}
              onChange={(e) => setMeta({ ...meta, fecha: e.target.value })}
              placeholder="Julio de 2026"
            />
          </label>
        </div>
      </div>

      {/* Bloques del cuestionario */}
      {cuestionario.bloques.map((bloque) => (
        <div className="stage" key={bloque.bloque}>
          <h2>{bloque.titulo}</h2>
          <p className="bloque-sub">{bloque.subtitulo}</p>

          {bloque.preguntas.map((p) =>
            p.tipo === "orden_propositos" ? (
              <div className="pregunta" key={p.id}>
                <p className="pregunta-texto">
                  <span className="pregunta-num">{p.id}</span>
                  {p.texto}
                </p>
                <OrdenPropositos
                  propositos={cuestionario.propositos}
                  orden={orden}
                  setOrden={setOrden}
                />
              </div>
            ) : (
              <div className="pregunta" key={p.id}>
                <p className="pregunta-texto">
                  <span className="pregunta-num">{p.id}</span>
                  {p.texto}
                </p>
                <textarea
                  className="respuesta"
                  rows={2}
                  value={respuestas[p.id]?.respuesta || ""}
                  onChange={(e) => setCampo(p.id, "respuesta", e.target.value)}
                  placeholder="Respuesta del entrevistado…"
                />
                <textarea
                  className="observaciones"
                  rows={1}
                  value={respuestas[p.id]?.observaciones || ""}
                  onChange={(e) => setCampo(p.id, "observaciones", e.target.value)}
                  placeholder="Observaciones del consultor (titubeos, molestias, contexto)…"
                />
              </div>
            )
          )}
        </div>
      ))}

      {/* Acciones */}
      <div className="acciones">
        <button className="btn-primario" onClick={generar} disabled={!listoParaAnalizar || analizando}>
          {analizando ? "El agente analiza…" : "Generar análisis del agente"}
        </button>
        <button className="btn-secundario" onClick={exportar}>
          {copiado ? "Copiado ✓" : "Exportar para analizar en Claude"}
        </button>
        <span className="gate-hint">
          {listoParaAnalizar
            ? "Listo para analizar."
            : `Se activa con 6 respuestas (${respondidas}/6) y el orden de propósitos (${orden.length}/3).`}
        </span>
      </div>

      {error && <div className="error-banner">⚠ {error}</div>}

      <Dictamen dictamen={dictamen} />
    </>
  );
}
