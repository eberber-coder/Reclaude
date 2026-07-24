import { useState } from "react";
import Consejo from "./components/Consejo.jsx";
import Capitulo1 from "./capitulo1/Capitulo1.jsx";

const VISTAS = {
  consejo: { etiqueta: "Consejo de LLMs", titulo: "Reclaude" },
  capitulo1: { etiqueta: "Capítulo 1 · Propósito", titulo: "Arquitectura de Consejo" },
};

export default function App() {
  const [vista, setVista] = useState("consejo");

  return (
    <div className="app">
      <header>
        <h1>{VISTAS[vista].titulo}</h1>
        <nav className="vista-nav">
          {Object.entries(VISTAS).map(([id, v]) => (
            <button
              key={id}
              className={`vista-tab${vista === id ? " active" : ""}`}
              onClick={() => setVista(id)}
            >
              {v.etiqueta}
            </button>
          ))}
        </nav>
      </header>

      {vista === "consejo" ? <Consejo /> : <Capitulo1 />}
    </div>
  );
}
