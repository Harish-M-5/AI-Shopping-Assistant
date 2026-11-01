"""OCR service: EasyOCR (default) or Tesseract, plus light image pre-processing."""
import threading
from functools import lru_cache

import cv2
import numpy as np

from ..config import settings
from .dates import extract_dates

MAX_SIDE = 1280  # downscale huge frames for speed


def _resize(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    scale = MAX_SIDE / max(h, w)
    return cv2.resize(img, None, fx=scale, fy=scale) if scale < 1 else img


def _preprocess(img: np.ndarray) -> np.ndarray:
    """Grayscale + contrast boost (CLAHE) + sharpen: helps with printed ink dates."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
    blur = cv2.GaussianBlur(gray, (0, 0), 3)
    return cv2.addWeighted(gray, 1.6, blur, -0.6, 0)


class OCRService:
    def __init__(self):
        self.engine = settings.OCR_ENGINE
        self._lock = threading.Lock()
        self._reader = None

    def _easyocr(self, img: np.ndarray) -> str:
        if self._reader is None:
            import easyocr  # lazy: model download/initialisation is slow
            self._reader = easyocr.Reader(settings.OCR_LANGS, gpu=settings.USE_GPU, verbose=False)
        with self._lock:
            return " ".join(self._reader.readtext(img, detail=0, paragraph=False))

    def _tesseract(self, img: np.ndarray) -> str:
        import pytesseract
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        return pytesseract.image_to_string(img, config="--psm 6").replace("\n", " ")

    def read_text(self, img: np.ndarray) -> str:
        run = self._tesseract if self.engine == "tesseract" else self._easyocr
        return run(img)

    def extract(self, image_bgr: np.ndarray) -> dict:
        """OCR the image and parse dates. Tries the raw image first, then an enhanced copy."""
        img = _resize(image_bgr)
        text = self.read_text(img)
        result = extract_dates(text)
        if not (result["manufacturing_date"] or result["expiry_date"]):
            enhanced = self.read_text(_preprocess(img))
            if enhanced:
                text = f"{text} {enhanced}"
                result = extract_dates(text)
        result["raw_text"] = text.strip()
        return result


@lru_cache(maxsize=1)
def get_ocr() -> OCRService:
    return OCRService()
