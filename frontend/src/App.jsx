import { useRef, useState } from "react";
import { streamCouncil } from "./sse.js";
import QueryInput from "./components/QueryInput.jsx";
import MemberAnswers from "./components/MemberAnswers.jsx";
import Rankings from "./components/Rankings.jsx";
import FinalAnswer from "./components/FinalAnswer.jsx";

export default function App() {
  const [query, setQuery] = useState("");
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [answers, setAnswers] = useState(null);
  const [rankings, setRankings] = useState(null);
  const [consensus, setConsensus] = useState(null);
  const [finalText, setFinalText] = useState("");
  const [chairman, setChairman] = useState(null);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  async function submit() {
    if (!query.trim() || loading) return;

    // Reiniciar estado.
    setLoading(true);
    setError(null);
    setAnswers(null);
    setRankings(null);
    setConsensus(null);
    setFinalText("");
    setChairman(null);
    setStreaming(false);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await streamCouncil(
        query,
        documents,
        (event, data) => {
          switch (event) {
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
        controller.signal
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
        documents={documents}
        setDocuments={setDocuments}
        onSubmit={submit}
        loading={loading}
      />

      {error && <div className="error-banner">⚠ {error}</div>}

      <MemberAnswers answers={answers} />
      <Rankings rankings={rankings} consensus={consensus} />
      <FinalAnswer text={finalText} chairman={chairman} streaming={streaming} />
    </div>
  );
}
