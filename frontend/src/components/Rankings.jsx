export default function Rankings({ rankings, consensus }) {
  if (!rankings) return null;

  return (
    <section className="stage">
      <h2>
        <span className="stage-num">2</span> Evaluación por pares (anónima)
      </h2>

      {consensus && consensus.length > 0 && (
        <div className="consensus">
          <h3>Consenso del consejo</h3>
          <ol className="consensus-list">
            {consensus.map((c) => (
              <li key={c.model}>
                <span className="consensus-name">{c.display_name}</span>
                <span className="consensus-score">
                  posición media:{" "}
                  {c.average_position === null ? "—" : c.average_position}
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}

      <div className="rankings-grid">
        {rankings.map((r) => (
          <div key={r.model} className={`ranking-card ${r.error ? "card-error" : ""}`}>
            <h4>{r.display_name} votó:</h4>
            {r.error ? (
              <p className="error-text">Error: {r.error}</p>
            ) : (
              <>
                <ol className="ranking-order">
                  {r.ranked_models.map((m, i) => (
                    <li key={i}>{displayName(rankings, consensus, m)}</li>
                  ))}
                </ol>
                <p className="rationale">{r.rationale}</p>
              </>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

// Busca el nombre legible de un modelo entre los datos disponibles.
function displayName(rankings, consensus, modelId) {
  const fromConsensus = consensus?.find((c) => c.model === modelId);
  if (fromConsensus) return fromConsensus.display_name;
  const fromRanking = rankings?.find((r) => r.model === modelId);
  if (fromRanking) return fromRanking.display_name;
  return modelId;
}
