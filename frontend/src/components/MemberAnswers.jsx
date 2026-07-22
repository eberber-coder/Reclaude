import { useState } from "react";

export default function MemberAnswers({ answers }) {
  const [active, setActive] = useState(0);
  if (!answers || answers.length === 0) return null;

  return (
    <section className="stage">
      <h2>
        <span className="stage-num">1</span> Respuestas individuales
      </h2>
      <div className="tabs">
        {answers.map((a, i) => (
          <button
            key={a.model}
            className={`tab ${i === active ? "active" : ""} ${a.error ? "tab-error" : ""}`}
            onClick={() => setActive(i)}
          >
            {a.display_name}
            {a.error ? " ⚠" : ""}
          </button>
        ))}
      </div>
      <div className="tab-panel">
        {answers[active]?.error ? (
          <p className="error-text">Error: {answers[active].error}</p>
        ) : (
          <pre className="answer-text">{answers[active]?.answer}</pre>
        )}
      </div>
    </section>
  );
}
