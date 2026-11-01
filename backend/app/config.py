"""Central configuration, loaded from environment variables / backend/.env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    # --- YOLO ---
    YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")
    YOLO_CONF = float(os.getenv("YOLO_CONF", "0.35"))
    YOLO_IMGSZ = int(os.getenv("YOLO_IMGSZ", "640"))

    # --- OCR ---
    OCR_ENGINE = os.getenv("OCR_ENGINE", "easyocr").lower()
    OCR_LANGS = [l.strip() for l in os.getenv("OCR_LANGS", "en").split(",") if l.strip()]
    USE_GPU = _bool("USE_GPU", False)
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")

    # --- LLM (provider-agnostic; see services/llm.py for the provider presets) ---
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")      # one generic key for whichever provider you pick
    LLM_MODEL = os.getenv("LLM_MODEL", "")          # optional: overrides the provider's default model
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")    # optional: required for LLM_PROVIDER=custom

    # --- Server ---
    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if o.strip()
    ]
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))


settings = Settings()
