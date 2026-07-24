import { useRef, useState } from "react";
import { streamCouncil } from "../sse.js";
import QueryInput from "./QueryInput.jsx";
import MemberAnswers from "./MemberAnswers.jsx";
import Rankings from "./Rankings.jsx";
import FinalAnswer from "./FinalAnswer.jsx";

// Vista del consejo de LLMs: varios modelos Claude deliberan, se evalúan entre
// sí y un chairman sintetiza la respuesta final.
export default function Consejo() {
  const [query, setQuery] = useState("");
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
    <>
      <p className="subtitle">
        Varios modelos Claude deliberan, se evalúan entre sí y un chairman
        sintetiza la respuesta final.
      </p>

      <QueryInput
        query={query}
        setQuery={setQuery}
        onSubmit={submit}
        loading={loading}
      />

      {error && <div className="error-banner">⚠ {error}</div>}

      <MemberAnswers answers={answers} />
      <Rankings rankings={rankings} consensus={consensus} />
      <FinalAnswer text={finalText} chairman={chairman} streaming={streaming} />
    </>
  );
}
