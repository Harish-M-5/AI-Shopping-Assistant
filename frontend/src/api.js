// Thin wrapper around the FastAPI backend.
const BASE = import.meta.env.VITE_API_URL || "/api";

async function post(path, form) {
  const res = await fetch(`${BASE}${path}`, { method: "POST", body: form });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch { /* ignore */ }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

/** Fast per-frame detection (YOLO + damage). */
export function detectFrame(blob) {
  const form = new FormData();
  form.append("file", blob, "frame.jpg");
  return post("/detect", form);
}

/** Full analysis: damage + OCR dates + generative AI insights. */
export function analyzeFrame(blob, { productName = "", detection = null } = {}) {
  const form = new FormData();
  form.append("file", blob, "frame.jpg");
  if (productName) form.append("product_name", productName);
  if (detection) {
    form.append("bbox", JSON.stringify(detection.bbox));
    form.append("confidence", String(detection.confidence));
  }
  return post("/analyze", form);
}

export async function getHealth() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error("offline");
  return res.json();
}
