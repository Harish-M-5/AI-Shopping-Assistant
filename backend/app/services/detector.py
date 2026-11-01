"""YOLOv8 product detector (thin wrapper around ultralytics)."""
import threading
from functools import lru_cache

import numpy as np

from ..config import settings


class ProductDetector:
    """Loads a YOLOv8 model once and runs inference on BGR numpy images."""

    def __init__(self, model_path: str, conf: float, imgsz: int):
        from ultralytics import YOLO  # imported lazily so the API boots fast

        # "yolov8n.pt" is downloaded automatically on the first run.
        self.model = YOLO(model_path)
        self.conf = conf
        self.imgsz = imgsz
        self._lock = threading.Lock()  # YOLO model is not guaranteed thread-safe

    def detect(self, image_bgr: np.ndarray) -> list[dict]:
        """Return a list of {label, confidence, box_px, bbox(normalised)} sorted by confidence."""
        h, w = image_bgr.shape[:2]
        with self._lock:
            result = self.model.predict(
                image_bgr, conf=self.conf, imgsz=self.imgsz, verbose=False
            )[0]

        detections = []
        for box in result.boxes:
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
            detections.append(
                {
                    "label": str(self.model.names[int(box.cls[0])]),
                    "confidence": round(float(box.conf[0]), 3),
                    "box_px": (int(x1), int(y1), int(x2), int(y2)),
                    "bbox": {"x1": x1 / w, "y1": y1 / h, "x2": x2 / w, "y2": y2 / h},
                }
            )
        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections


@lru_cache(maxsize=1)
def get_detector() -> ProductDetector:
    """Singleton accessor – the model is loaded on first use."""
    return ProductDetector(settings.YOLO_MODEL, settings.YOLO_CONF, settings.YOLO_IMGSZ)
