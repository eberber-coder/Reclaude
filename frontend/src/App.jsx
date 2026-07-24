import { useRef, useState } from "react";
import { streamCouncil } from "./sse.js";
import QueryInput from "./components/QueryInput.jsx";
import MemberAnswers from "./components/MemberAnswers.jsx";
import Rankings from "./components/Rankings.jsx";
import FinalAnswer from "./components/FinalAnswer.jsx";

// Lee un File del navegador y lo convierte en un adjunto (bytes en base64).
function readFileAsAttachment(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      // FileReader devuelve un data URL "data:<mime>;base64,<datos>".
      const base64 = String(reader.result).split(",", 2)[1] || "";
      resolve({
        filename: file.name,
        media_type: file.type || "application/octet-stream",
        data: base64,
        size: file.size,
      });
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export default function App() {
  const [query, setQuery] = useState("");
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [answers, setAnswers] = useState(null);
  const [rankings, setRankings] = useState(null);
  const [consensus, setConsensus] = useState(null);
  const [finalText, setFinalText] = useState("");
  const [chairman, setChairman] = useState(null);
  const [streaming, setStreaming] = useState(false);
  const [warnings, setWarnings] = useState([]);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  async function addFiles(files) {
    try {
      const read = await Promise.all(files.map(readFileAsAttachment));
      setAttachments((prev) => [...prev, ...read]);
    } catch (e) {
      setError(`No se pudo leer un archivo: ${e?.message || e}`);
    }
  }

  function removeAttachment(index) {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  }

  async function submit() {
    if (!query.trim() || loading) return;

    // Reiniciar estado.
    setLoading(true);
    setError(null);
    setWarnings([]);
    setAnswers(null);
    setRankings(null);
    setConsensus(null);
    setFinalText("");
    setChairman(null);
    setStreaming(false);

    const controller = new AbortController();
    abortRef.current = controller;

    // El backend solo necesita filename/media_type/data (el tamaño es de la UI).
    const payload = attachments.map(({ filename, media_type, data }) => ({
      filename,
      media_type,
      data,
    }));

    try {
      await streamCouncil(
        query,
        (event, data) => {
          switch (event) {
            case "attachments":
              setWarnings(data.warnings || []);
              break;
            case "members":
              setAnswers(data.answers);
              break;
            case "rankings":
              setRankings(data.rankings);
              setConsensus(data.consensus);
              setStreaming(true);
              break;
            case "final_delta":
              setFinalText((prev) => prev + data.text);
              break;
            case "done":
              setChairman(data.chairman);
              setStreaming(false);
              break;
            case "error":
              setError(data.message);
              break;
            default:
              break;
          }
        },
        controller.signal,
        payload
      );
    } catch (e) {
      if (e.name !== "AbortError") setError(e.message);
    } finally {
      setStreaming(false);
      setLoading(false);
      abortRef.current = null;
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Reclaude</h1>
        <p className="subtitle">
          Metodología de consejo — varios modelos Claude deliberan, se evalúan
          entre sí y un chairman sintetiza la respuesta final.
        </p>
      </header>

      <QueryInput
        query={query}
        setQuery={setQuery}
        onSubmit={submit}
        loading={loading}
        attachments={attachments}
        onAddFiles={addFiles}
        onRemoveAttachment={removeAttachment}
      />

      {error && <div className="error-banner">⚠ {error}</div>}

      {warnings.length > 0 && (
        <div className="warning-banner">
          {warnings.map((w, i) => (
            <div key={i}>⚠ {w}</div>
          ))}
        </div>
      )}

      <MemberAnswers answers={answers} />
      <Rankings rankings={rankings} consensus={consensus} />
      <FinalAnswer text={finalText} chairman={chairman} streaming={streaming} />
    </div>
  );
}
