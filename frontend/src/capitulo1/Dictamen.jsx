// Muestra el dictamen preliminar del agente. Siempre rotulado como sujeto al
// juicio del consultor: el agente pondera y propone; el consultor decide.

function claseRecomendacion(decision = "") {
  const d = decision.toLowerCase();
  if (d.includes("esperar")) return "rec-esperar";
  if (d.includes("reserva")) return "rec-reservas";
  if (d.includes("proceder")) return "rec-proceder";
  return "";
}

export default function Dictamen({ dictamen }) {
  if (!dictamen) return null;

  const {
    semaforos = [],
    proposito_dominante,
    propositos_secundarios = [],
    puntos_devolucion = [],
    borrador_declaracion = "",
    recomendacion,
  } = dictamen;

  return (
    <section className="stage dictamen">
      <h2>
        <span className="stage-num">✓</span> Dictamen del agente
      </h2>

      <p className="preliminar">
        Preliminar, sujeto al juicio del consultor. El agente pondera y propone;
        el consultor califica y decide.
      </p>

      <h3 className="dic-sub">Semáforos</h3>
      <div className="semaforos">
        {semaforos.map((s, i) => (
          <div key={i} className={`semaforo sem-${(s.color || "").toLowerCase()}`}>
            <div className="sem-cabecera">
              <span className="sem-punto" aria-hidden="true" />
              <span className="sem-nombre">{s.nombre}</span>
              <span className="sem-color">{s.color}</span>
            </div>
            <p className="sem-fundamento">{s.fundamento}</p>
          </div>
        ))}
      </div>

      <h3 className="dic-sub">Jerarquía de propósitos</h3>
      {proposito_dominante && (
        <div className="prop-dominante">
          <span className="prop-etiqueta">Dominante</span>
          <strong>{proposito_dominante.proposito}</strong>
          <p className="rationale">{proposito_dominante.fundamento}</p>
        </div>
      )}
      {propositos_secundarios.map((p, i) => (
        <div key={i} className="prop-secundario">
          <span className="prop-etiqueta secundaria">Secundario</span>
          <strong>{p.proposito}</strong>
          <p className="rationale">{p.fundamento}</p>
        </div>
      ))}

      <h3 className="dic-sub">Puntos para la sesión de devolución</h3>
      <ul className="devolucion">
        {puntos_devolucion.map((punto, i) => (
          <li key={i}>{punto}</li>
        ))}
      </ul>

      <h3 className="dic-sub">Borrador de declaración de propósito</h3>
      <pre className="answer-text borrador">{borrador_declaracion}</pre>

      {recomendacion && (
        <div className={`recomendacion ${claseRecomendacion(recomendacion.decision)}`}>
          <span className="rec-decision">{recomendacion.decision}</span>
          <p className="rec-fundamento">{recomendacion.fundamento}</p>
        </div>
      )}
    </section>
  );
}
