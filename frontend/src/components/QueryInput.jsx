import { useRef } from "react";

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function QueryInput({
  query,
  setQuery,
  onSubmit,
  loading,
  attachments,
  onAddFiles,
  onRemoveAttachment,
}) {
  const fileRef = useRef(null);

  function handleKeyDown(e) {
    // Enviar con Ctrl/Cmd + Enter.
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (!loading) onSubmit();
    }
  }

  function handleFiles(e) {
    const files = Array.from(e.target.files || []);
    if (files.length) onAddFiles(files);
    // Permitir volver a seleccionar el mismo archivo después.
    e.target.value = "";
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

      {attachments.length > 0 && (
        <ul className="attachments">
          {attachments.map((att, i) => (
            <li key={`${att.filename}-${i}`} className="attachment-chip">
              <span className="attachment-name" title={att.filename}>
                📎 {att.filename}
              </span>
              <span className="attachment-size">{formatSize(att.size)}</span>
              {!loading && (
                <button
                  type="button"
                  className="attachment-remove"
                  onClick={() => onRemoveAttachment(i)}
                  aria-label={`Quitar ${att.filename}`}
                >
                  ✕
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="query-actions">
        <button
          type="button"
          className="attach-btn"
          onClick={() => fileRef.current?.click()}
          disabled={loading}
        >
          + Adjuntar archivos
        </button>
        <input
          ref={fileRef}
          type="file"
          multiple
          hidden
          onChange={handleFiles}
          accept=".pdf,.txt,.md,.csv,.json,.log,.py,.js,.ts,.jsx,.tsx,.html,.css,.yaml,.yml,.xml,image/*,text/*,application/pdf"
        />
        <button onClick={onSubmit} disabled={loading || !query.trim()}>
          {loading ? "El consejo delibera…" : "Consultar al consejo (⌘/Ctrl + ⏎)"}
        </button>
      </div>
    </div>
  );
}
