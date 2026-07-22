export default function FinalAnswer({ text, chairman, streaming }) {
  if (!text && !streaming) return null;

  return (
    <section className="stage final">
      <h2>
        <span className="stage-num">3</span> Respuesta final del chairman
        {chairman ? ` — ${chairman}` : ""}
      </h2>
      <pre className="answer-text final-text">
        {text}
        {streaming && <span className="cursor">▋</span>}
      </pre>
    </section>
  );
}
