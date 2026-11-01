import { useCallback, useEffect, useRef, useState } from "react";
import { analyzeFrame, detectFrame, getHealth } from "../api.js";
import ResultPanel from "../components/ResultPanel.jsx";
import { drawBoxes } from "../utils.js";

const DETECT_INTERVAL_MS = 600; // ~1.5 detections / second keeps CPU inference smooth

export default function Detect() {
  // --- refs: media elements, overlay canvas, offscreen capture canvas ---
  const videoRef = useRef(null);
  const imgRef = useRef(null);
  const overlayRef = useRef(null);
  const grabRef = useRef(null);
  const busyRef = useRef(false); // prevents overlapping detect requests

  // --- state ---
  const [mode, setMode] = useState("camera"); // "camera" | "image"
  const [running, setRunning] = useState(false);
  const [aspect, setAspect] = useState(16 / 9);
  const [imageUrl, setImageUrl] = useState(null);
  const [detections, setDetections] = useState([]);
  const [pickedLabel, setPickedLabel] = useState(null);
  const [latency, setLatency] = useState(null);
  const [manualName, setManualName] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState(null);

  // The product the user picked (defaults to the most confident detection).
  const selected = detections.find((d) => d.label === pickedLabel) || detections[0] || null;

  useEffect(() => { getHealth().then(setHealth).catch(() => setHealth({ status: "offline" })); }, []);

  /** Grab the current video frame / image as a JPEG blob (downscaled to maxSide). */
  const captureBlob = useCallback((maxSide, quality) => new Promise((resolve) => {
    const el = mode === "camera" ? videoRef.current : imgRef.current;
    const w = el?.videoWidth || el?.naturalWidth;
    const h = el?.videoHeight || el?.naturalHeight;
    if (!w || !h) return resolve(null);
    const canvas = (grabRef.current ??= document.createElement("canvas"));
    const scale = Math.min(1, maxSide / Math.max(w, h));
    canvas.width = Math.round(w * scale);
    canvas.height = Math.round(h * scale);
    canvas.getContext("2d").drawImage(el, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(resolve, "image/jpeg", quality);
  }), [mode]);

  // --- camera control ---
  async function startCamera() {
    setError("");
    setMode("camera");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      const v = videoRef.current;
      v.srcObject = stream;
      await v.play();
      setAspect(v.videoWidth / v.videoHeight || 16 / 9);
      setRunning(true);
    } catch (e) {
      setError(`Camera unavailable (${e.message}). Allow permission and use http://localhost or HTTPS.`);
    }
  }

  function stopCamera() {
    videoRef.current?.srcObject?.getTracks().forEach((t) => t.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
    setRunning(false);
    setDetections([]);
  }
  useEffect(() => () => stopCamera(), []); // release the camera when leaving the page

  // --- live detection loop ---
  const runDetect = useCallback(async () => {
    if (busyRef.current) return;
    busyRef.current = true;
    try {
      const blob = await captureBlob(640, 0.7);
      if (!blob) return;
      const r = await detectFrame(blob);
      setDetections(r.detections);
      setLatency(r.inference_ms);
      setError("");
    } catch (e) {
      setError(`Detection failed: ${e.message}`);
    } finally {
      busyRef.current = false;
    }
  }, [captureBlob]);

  useEffect(() => {
    if (!running || mode !== "camera") return;
    const id = setInterval(runDetect, DETECT_INTERVAL_MS);
    return () => clearInterval(id);
  }, [running, mode, runDetect]);

  // --- redraw boxes whenever detections change or the window is resized ---
  useEffect(() => {
    const draw = () => drawBoxes(overlayRef.current, detections, selected?.id);
    draw();
    window.addEventListener("resize", draw);
    return () => window.removeEventListener("resize", draw);
  }, [detections, selected?.id, aspect]);

  // --- image upload mode (handy for testing without a camera) ---
  function onFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    stopCamera();
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    setImageUrl(URL.createObjectURL(file));
    setMode("image");
    setDetections([]);
    setAnalysis(null);
    e.target.value = "";
  }

  // --- full analysis (damage + OCR + LLM) ---
  async function onAnalyze() {
    setError("");
    setAnalyzing(true);
    setAnalysis(null);
    try {
      const blob = await captureBlob(1280, 0.92); // higher resolution so small date text stays readable
      if (!blob) throw new Error("No frame available – start the camera or upload an image first.");
      const name = manualName.trim();
      setAnalysis(await analyzeFrame(blob, { productName: name || selected?.label || "", detection: name ? null : selected }));
    } catch (e) {
      setError(e.message);
    } finally {
      setAnalyzing(false);
    }
  }

  const hasMedia = (mode === "camera" && running) || (mode === "image" && imageUrl);

  return (
    <>
      <h1 className="page-title">Live Camera Detection</h1>
      {health?.status === "offline" && (
        <p className="notice bad">Backend is offline. Start it with <code>uvicorn app.main:app --reload</code> in <code>backend/</code>.</p>
      )}
      {error && <p className="notice bad">{error}</p>}

      <div className="detect-layout">
        <div>
          {/* Camera / image stage with canvas overlay */}
          <div className="stage card" style={{ aspectRatio: aspect }}>
            <video ref={videoRef} playsInline muted style={{ display: mode === "camera" ? "block" : "none" }} />
            {mode === "image" && imageUrl && (
              <img
                ref={imgRef}
                src={imageUrl}
                alt="Uploaded product"
                onLoad={(e) => { setAspect(e.target.naturalWidth / e.target.naturalHeight); runDetect(); }}
              />
            )}
            <canvas ref={overlayRef} className="overlay" />
            {!hasMedia && <div className="placeholder">📷<p>Start the camera or upload an image</p></div>}
          </div>

          <div className="controls">
            {running
              ? <button className="btn" onClick={stopCamera}>■ Stop camera</button>
              : <button className="btn btn-primary" onClick={startCamera}>▶ Start camera</button>}
            <label className="btn">
              🖼 Upload image
              <input type="file" accept="image/*" hidden onChange={onFile} />
            </label>
            <button className="btn btn-accent" onClick={onAnalyze} disabled={!hasMedia || analyzing}>
              {analyzing ? "Analyzing…" : "✨ Analyze product"}
            </button>
          </div>

          <div className="card detections">
            <div className="row">
              <h3>Detected products</h3>
              {latency != null && <span className="muted">{latency} ms / frame</span>}
            </div>
            {detections.length === 0 && <p className="muted">Nothing detected yet.</p>}
            <div className="chips">
              {detections.map((d) => (
                <button
                  key={d.id}
                  className={`chip ${d.id === selected?.id ? "active" : ""} ${d.damage.is_damaged ? "dmg" : ""}`}
                  onClick={() => setPickedLabel(d.label)}
                >
                  {d.label} · {Math.round(d.confidence * 100)}%{d.damage.is_damaged ? " ⚠" : ""}
                </button>
              ))}
            </div>
            <input
              className="input"
              placeholder="Or type a product name manually"
              value={manualName}
              onChange={(e) => setManualName(e.target.value)}
            />
            <small className="muted">
              Yolo
            </small>
          </div>
        </div>

        <ResultPanel analysis={analysis} loading={analyzing} />
      </div>
    </>
  );
}
