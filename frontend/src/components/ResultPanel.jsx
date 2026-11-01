import { formatDate } from "../utils.js";

const STATUS = {
  ok: ["Fresh", "good"],
  expiring_soon: ["Expiring soon", "warn"],
  expired: ["Expired", "bad"],
  unknown: ["Dates not found", "muted"],
};

const Badge = ({ tone, children }) => <span className={`badge ${tone}`}>{children}</span>;

const Section = ({ title, children }) => (
  <section className="rsec">
    <h4>{title}</h4>
    {children}
  </section>
);

const List = ({ items = [] }) => (
  <ul>{items.map((t, i) => <li key={i}>{t}</li>)}</ul>
);

/** AI Result Panel: damage verdict, OCR dates and generative-AI insights. */
export default function ResultPanel({ analysis, loading }) {
  if (loading) {
    return (
      <aside className="card result">
        <h3>AI Result</h3>
        <div className="skeleton" /><div className="skeleton" /><div className="skeleton short" />
        <p className="muted">Reading label, checking packaging and asking the AI…</p>
      </aside>
    );
  }

  if (!analysis) {
    return (
      <aside className="card result empty">
        <h3>AI Result</h3>
        <p className="muted">Point the camera at a product, then press <b>Analyze product</b>. Results appear here.</p>
      </aside>
    );
  }

  const { product, damage, dates, ai, meta, message } = analysis;
  const [statusText, statusTone] = STATUS[dates.status] || STATUS.unknown;
  const nutrition = ai?.nutrition;

  return (
    <aside className="card result">
      <header className="rhead">
        <div>
          <h3 className="cap">{product.name}</h3>
          {product.confidence != null && <span className="muted">Confidence {Math.round(product.confidence * 100)}%</span>}
        </div>
        <Badge tone={damage.is_damaged ? "bad" : "good"}>{damage.is_damaged ? "Damaged" : "Packaging OK"}</Badge>
      </header>

      {message && <p className="notice">{message}</p>}
      {meta?.llm_used === false && (
        <p className="notice">
          {meta.reason === "no_api_key"
            ? "No AI provider key configured – showing basic offline text. Set LLM_PROVIDER and LLM_API_KEY in backend/.env (see README)."
            : `AI service error – showing offline text. ${meta.error || ""}`}
        </p>
      )}

      <Section title="Packaging check">
        <p>
          {damage.is_damaged ? "Possible damage detected" : "No visible damage detected"}{" "}
          <span className="muted">(score {damage.score})</span>
        </p>
        {damage.reasons?.length > 0 && <List items={damage.reasons} />}
      </Section>

      <Section title="Dates (OCR)">
        <div className="dates">
          <div><span className="muted">Manufactured</span><b>{formatDate(dates.manufacturing_date)}</b></div>
          <div><span className="muted">Expiry</span><b>{formatDate(dates.expiry_date)}</b></div>
          <div>
            <span className="muted">Status</span>
            <Badge tone={statusTone}>{statusText}</Badge>
            {dates.days_left != null && (
              <small className="muted">
                {dates.days_left < 0 ? `${-dates.days_left} days ago` : `${dates.days_left} days left`}
              </small>
            )}
          </div>
        </div>
        {dates.raw_text && (
          <details>
            <summary>Raw OCR text</summary>
            <p className="raw">{dates.raw_text}</p>
          </details>
        )}
      </Section>

      {ai && (
        <>
          <Section title="Description"><p>{ai.description}</p></Section>
          <Section title="Main uses"><List items={ai.main_uses} /></Section>

          {nutrition && Array.isArray(nutrition.items) && (
            <Section title={`Basic nutrition${nutrition.per ? ` (per ${nutrition.per})` : ""}`}>
              <table className="nutri">
                <tbody>
                  {nutrition.items.map((n, i) => (
                    <tr key={i}><td>{n.label}</td><td>{n.value}</td></tr>
                  ))}
                </tbody>
              </table>
              {nutrition.note && <small className="muted">{nutrition.note}</small>}
            </Section>
          )}

          <Section title="Storage tips"><List items={ai.storage_tips} /></Section>
          <div className="advice"><b>🛍️ Shopping advice</b><p>{ai.shopping_advice}</p></div>
          {meta?.llm_used && <p className="muted">AI by {meta.provider} · {meta.model}</p>}
        </>
      )}
    </aside>
  );
}
