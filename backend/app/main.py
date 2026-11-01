"""FastAPI entry point.

Endpoints
  GET  /api/health    - liveness + config summary
  POST /api/detect    - YOLO detection + per-object damage check (called ~2x/second by the live camera)
  POST /api/analyze   - full pipeline for one frame: product -> damage -> OCR dates -> LLM insights
"""
import json
import time
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import AnalyzeResponse, DetectResponse
from .services.damage import assess_damage
from .services.detector import get_detector
from .services.llm import generate_product_info, llm_status
from .services.ocr import get_ocr

app = FastAPI(title="AI Smart Shopping Assistant", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- helpers
async def _read_image(file: UploadFile) -> np.ndarray:
    """Decode an uploaded image into a BGR numpy array (with size/format validation)."""
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"Image larger than {settings.MAX_UPLOAD_MB} MB")
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "Could not decode image")
    return img


def _crop(img: np.ndarray, bbox: dict, pad: float = 0.02) -> np.ndarray:
    """Crop a normalised bbox (with a little padding) out of the image."""
    h, w = img.shape[:2]
    x1, y1 = int(max(0, (bbox["x1"] - pad) * w)), int(max(0, (bbox["y1"] - pad) * h))
    x2, y2 = int(min(w, (bbox["x2"] + pad) * w)), int(min(h, (bbox["y2"] + pad) * h))
    return img[y1:y2, x1:x2]


def _detect_sync(img: np.ndarray) -> dict:
    t0 = time.perf_counter()
    raw = get_detector().detect(img)
    out = []
    for i, d in enumerate(raw):
        out.append(
            {
                "id": i,
                "label": d["label"],
                "confidence": d["confidence"],
                "bbox": d["bbox"],
                "damage": assess_damage(_crop(img, d["bbox"]), d["label"]),
            }
        )
    h, w = img.shape[:2]
    return {
        "width": w,
        "height": h,
        "inference_ms": round((time.perf_counter() - t0) * 1000, 1),
        "detections": out,
    }


def _vision_sync(img: np.ndarray, product_name: str, bbox: Optional[dict], confidence: Optional[float]) -> dict:
    """Detection (if needed) + damage + OCR. Runs in a worker thread (CPU heavy)."""
    name, conf = product_name, confidence
    if bbox is None:
        dets = get_detector().detect(img)
        if dets:  # use the most confident detection
            top = dets[0]
            bbox, conf = top["bbox"], top["confidence"]
            name = name or top["label"]

    crop = _crop(img, bbox) if bbox else img
    damage = assess_damage(crop, name)
    dates = get_ocr().extract(img)  # dates may sit outside the YOLO box, so OCR the full frame
    return {"name": name, "confidence": conf, "bbox": bbox, "damage": damage, "dates": dates}


# --------------------------------------------------------------------------- routes
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "yolo_model": settings.YOLO_MODEL,
        "ocr_engine": settings.OCR_ENGINE,
        **llm_status(),  # llm_provider, llm_model, llm_configured
    }


@app.post("/api/detect", response_model=DetectResponse)
async def detect(file: UploadFile = File(...)):
    """Detect products in one frame and flag visibly damaged ones."""
    img = await _read_image(file)
    return await run_in_threadpool(_detect_sync, img)


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile = File(...),
    product_name: str = Form(""),
    bbox: str = Form(""),           # optional JSON {"x1","y1","x2","y2"} (normalised)
    confidence: str = Form(""),     # optional detection confidence from the live view
):
    """Full analysis of a single frame, including generative-AI shopping insights."""
    img = await _read_image(file)
    try:
        box = json.loads(bbox) if bbox else None
        conf = float(confidence) if confidence else None
    except (ValueError, TypeError):
        raise HTTPException(400, "Invalid bbox / confidence")

    v = await run_in_threadpool(_vision_sync, img, product_name.strip(), box, conf)

    if not v["name"]:
        return {
            "product": {"name": "Unknown product"},
            "damage": v["damage"],
            "dates": v["dates"],
            "ai": None,
            "meta": {},
            "message": "No product detected. Type a product name and analyze again.",
        }

    ai, meta = await generate_product_info(v["name"], v["damage"], v["dates"])
    meta["ocr_engine"] = settings.OCR_ENGINE
    return {
        "product": {"name": v["name"], "confidence": v["confidence"], "bbox": v["bbox"]},
        "damage": v["damage"],
        "dates": v["dates"],
        "ai": ai,
        "meta": meta,
    }
