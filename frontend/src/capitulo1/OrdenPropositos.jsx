// Pregunta 10: tarjetas de los seis propósitos que se ordenan 1º, 2º, 3º.
// Interacción por toque (sin arrastrar), para que funcione bien en iPad/iPhone:
// tocar una tarjeta le asigna el siguiente lugar disponible; volver a tocarla la
// quita y los demás rangos se recalculan.

const ORDINALES = ["1º", "2º", "3º"];

export default function OrdenPropositos({ propositos, orden, setOrden }) {
  function toggle(id) {
    const pos = orden.indexOf(id);
    if (pos !== -1) {
      setOrden(orden.filter((x) => x !== id));
    } else if (orden.length < 3) {
      setOrden([...orden, id]);
    }
  }

  return (
    <div className="propositos">
      {propositos.map((p) => {
        const pos = orden.indexOf(p.id);
        const seleccionado = pos !== -1;
        const lleno = orden.length >= 3;
        return (
          <button
            type="button"
            key={p.id}
            className={`proposito-card${seleccionado ? " seleccionado" : ""}`}
            onClick={() => toggle(p.id)}
            disabled={!seleccionado && lleno}
            aria-pressed={seleccionado}
          >
            <span className="proposito-rank">
              {seleccionado ? ORDINALES[pos] : ""}
            </span>
            <span className="proposito-cuerpo">
              <span className="proposito-nombre">{p.nombre}</span>
              <span className="proposito-desc">{p.descripcion}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
