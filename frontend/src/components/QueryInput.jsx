export default function QueryInput({ query, setQuery, onSubmit, loading }) {
  function handleKeyDown(e) {
    // Enviar con Ctrl/Cmd + Enter.
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (!loading) onSubmit();
    }
  }

  return (
    <div className="query-input">
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Escribe tu pregunta para el consejo…"
        rows={3}
        disabled={loading}
      />
      <button onClick={onSubmit} disabled={loading || !query.trim()}>
        {loading ? "El consejo delibera…" : "Consultar al consejo (⌘/Ctrl + ⏎)"}
      </button>
    </div>
  );
}
