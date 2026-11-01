import { Link } from "react-router-dom";

const FEATURES = [
  { icon: "🎯", title: "Live product detection", text: "YOLOv8 spots products in your camera feed and draws labelled boxes with confidence scores." },
  { icon: "🩹", title: "Damage check", text: "Flags torn packets, crushed boxes and dented packaging with OpenCV (demo-level)." },
  { icon: "📅", title: "Date reading (OCR)", text: "Reads Manufacturing and Expiry dates from the label and tells you if it is still fresh." },
  { icon: "✨", title: "AI shopping insights", text: "Get a description, main uses, basic nutrition, storage tips and quick buying advice." },
];

const STEPS = ["Open the camera and point it at a product.", "Pick the detected product and press Analyze.", "Read the AI result panel and shop with confidence."];

export default function Home() {
  return (
    <>
      <section className="hero">
        <h1>Scan it. Check it. <span>Shop smarter.</span></h1>
        <p>
          An AI assistant that recognises products through your camera, checks packaging for damage,
          reads expiry dates and explains what you are buying.
        </p>
        <Link to="/detect" className="btn btn-primary btn-lg">Start live detection →</Link>
      </section>

      <section className="grid features">
        {FEATURES.map((f) => (
          <article className="card" key={f.title}>
            <div className="icon">{f.icon}</div>
            <h3>{f.title}</h3>
            <p>{f.text}</p>
          </article>
        ))}
      </section>

      <section className="card how">
        <h2>How it works</h2>
        <ol>{STEPS.map((s) => <li key={s}>{s}</li>)}</ol>
      </section>
    </>
  );
}
