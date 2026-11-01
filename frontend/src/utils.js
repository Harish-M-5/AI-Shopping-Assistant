/** Draw YOLO boxes on an overlay <canvas>. Boxes arrive normalised (0..1), so they scale with the video. */
export function drawBoxes(canvas, detections, selectedId) {
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  ctx.font = "600 14px system-ui, sans-serif";
  ctx.textBaseline = "middle";

  for (const d of detections) {
    const { x1, y1, x2, y2 } = d.bbox;
    const x = x1 * w, y = y1 * h, bw = (x2 - x1) * w, bh = (y2 - y1) * h;
    const damaged = d.damage?.is_damaged;
    const color = damaged ? "#ef4444" : "#22c55e";

    ctx.lineWidth = d.id === selectedId ? 4 : 2.5;
    ctx.strokeStyle = color;
    ctx.strokeRect(x, y, bw, bh);

    // Label tag: "bottle 91%" (+ DAMAGED)
    const text = `${d.label} ${Math.round(d.confidence * 100)}%${damaged ? " • DAMAGED" : ""}`;
    const tw = ctx.measureText(text).width + 12;
    const ty = y - 24 < 0 ? y : y - 24; // keep tag on screen
    ctx.fillStyle = color;
    ctx.fillRect(x, ty, tw, 24);
    ctx.fillStyle = "#fff";
    ctx.fillText(text, x + 6, ty + 12);
  }
}

export const formatDate = (iso) =>
  iso ? new Date(iso + "T00:00:00").toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" }) : "—";
