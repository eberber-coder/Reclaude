import { useRef } from "react";

// Extensiones de texto admitidas para adjuntar como contexto.
const ACCEPT = ".md,.markdown,.txt,.mdx,text/markdown,text/plain";

export default function QueryInput({
  query,
  setQuery,
  documents,
  setDocuments,
  onSubmit,
  loading,
}) {
  const fileInputRef = useRef(null);

  function handleKeyDown(e) {
    // Enviar con Ctrl/Cmd + Enter.
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (!loading) onSubmit();
    }
  }

  function readFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve({ name: file.name, content: reader.result });
      reader.onerror = () => reject(reader.error);
      reader.readAsText(file);
    });
  }

  async function addFiles(fileList) {
    const files = Array.from(fileList || []);
    if (files.length === 0) return;
    const read = await Promise.all(files.map(readFile));
    setDocuments((prev) => {
      // Evitar duplicados por nombre; los nuevos reemplazan a los previos.
      const byName = new Map(prev.map((d) => [d.name, d]));
      for (const doc of read) byName.set(doc.name, doc);
      return Array.from(byName.values());
    });
  }

  async function handleFileChange(e) {
    await addFiles(e.target.files);
    // Permitir volver a elegir el mismo archivo después.
    e.target.value = "";
  }

  function removeDocument(name) {
    setDocuments((prev) => prev.filter((d) => d.name !== name));
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

      {documents.length > 0 && (
        <ul className="attachments">
          {documents.map((doc) => (
            <li key={doc.name} className="attachment">
              <span className="attachment-name" title={doc.name}>
                📄 {doc.name}
              </span>
              <span className="attachment-size">
                {formatChars(doc.content.length)}
              </span>
              <button
                type="button"
                className="attachment-remove"
                onClick={() => removeDocument(doc.name)}
                disabled={loading}
                aria-label={`Quitar ${doc.name}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="query-actions">
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT}
          multiple
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
        <button
          type="button"
          className="attach-button"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
        >
          📎 Adjuntar archivos MD
        </button>
        <button onClick={onSubmit} disabled={loading || !query.trim()}>
          {loading ? "El consejo delibera…" : "Consultar al consejo (⌘/Ctrl + ⏎)"}
        </button>
      </div>
    </div>
  );
}

function formatChars(n) {
  if (n < 1000) return `${n} car.`;
  return `${(n / 1000).toFixed(1)}k car.`;
}
