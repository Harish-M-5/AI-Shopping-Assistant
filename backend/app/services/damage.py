"""Demo-level damage detection using classical OpenCV heuristics.

How it works (on the cropped product region):
  1. Edge density   - crumpled / torn packaging has many irregular edges.
  2. Solidity       - area / convex-hull area of the silhouette; dents, rips and
                      broken corners make the outline non-convex.
  3. Texture energy - variance of the Laplacian; creases and cracks raise it.

These signals are combined into a 0..1 score. This is a *demo* heuristic, not a
quality-control system. For production accuracy, fine-tune YOLO with classes
such as `damaged_box` / `torn_packet` - any detected label containing a word in
DAMAGE_KEYWORDS is automatically flagged as damaged.
"""
import cv2
import numpy as np

DAMAGE_KEYWORDS = ("damaged", "torn", "broken", "crushed", "dented", "leak")
IS_DAMAGED_THRESHOLD = 0.5


def _clip01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def _solidity(blur: np.ndarray) -> float:
    """Solidity of the largest foreground blob (1.0 = perfectly convex)."""
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Make sure the *background* (image border) is black.
    border = np.concatenate([mask[0], mask[-1], mask[:, 0], mask[:, -1]])
    if border.mean() > 127:
        mask = cv2.bitwise_not(mask)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 1.0
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < 0.05 * mask.shape[0] * mask.shape[1]:
        return 1.0  # too small to judge reliably
    hull_area = cv2.contourArea(cv2.convexHull(largest))
    return float(area / hull_area) if hull_area > 0 else 1.0


def assess_damage(crop_bgr: "np.ndarray | None", label: str = "") -> dict:
    """Return {is_damaged, score, reasons} for a cropped product image."""
    # Custom-trained models: trust the class name.
    if any(k in label.lower() for k in DAMAGE_KEYWORDS):
        return {"is_damaged": True, "score": 0.95, "reasons": [f"Model class '{label}'"]}

    if crop_bgr is None or crop_bgr.size == 0 or min(crop_bgr.shape[:2]) < 24:
        return {"is_damaged": False, "score": 0.0, "reasons": []}

    # Normalise size so thresholds behave the same for near/far objects.
    h, w = crop_bgr.shape[:2]
    scale = 256.0 / max(h, w)
    small = cv2.resize(crop_bgr, (max(1, int(w * scale)), max(1, int(h * scale))))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    edge_density = float((cv2.Canny(blur, 60, 160) > 0).mean())
    solidity = _solidity(blur)
    lap_var = float(cv2.Laplacian(blur, cv2.CV_64F).var())

    s_edge = _clip01((edge_density - 0.07) / 0.08)
    s_solid = _clip01((0.93 - solidity) / 0.10)
    s_tex = _clip01((lap_var - 300.0) / 700.0)
    score = 0.4 * s_edge + 0.4 * s_solid + 0.2 * s_tex

    reasons = []
    if s_edge > 0.4:
        reasons.append("Crumpled or torn surface texture")
    if s_solid > 0.4:
        reasons.append("Irregular / dented outline")
    if s_tex > 0.5:
        reasons.append("Creases or cracks detected")

    return {
        "is_damaged": score >= IS_DAMAGED_THRESHOLD,
        "score": round(score, 2),
        "reasons": reasons,
    }
