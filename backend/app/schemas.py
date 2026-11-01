"""Pydantic response models (these also drive the auto-generated /docs page)."""
from typing import Any, Optional

from pydantic import BaseModel


class BBox(BaseModel):
    """Bounding box in *normalised* coordinates (0..1) so the UI can scale it freely."""
    x1: float
    y1: float
    x2: float
    y2: float


class DamageInfo(BaseModel):
    is_damaged: bool
    score: float                # 0 (pristine) .. 1 (badly damaged)
    reasons: list[str] = []


class Detection(BaseModel):
    id: int
    label: str
    confidence: float
    bbox: BBox
    damage: DamageInfo


class DetectResponse(BaseModel):
    width: int
    height: int
    inference_ms: float
    detections: list[Detection]


class DatesInfo(BaseModel):
    manufacturing_date: Optional[str] = None   # ISO yyyy-mm-dd
    expiry_date: Optional[str] = None          # ISO yyyy-mm-dd
    unlabeled_dates: list[str] = []
    status: str = "unknown"                    # ok | expiring_soon | expired | unknown
    days_left: Optional[int] = None
    raw_text: str = ""


class AIInfo(BaseModel):
    description: str = ""
    main_uses: list[str] = []
    nutrition: Optional[dict[str, Any]] = None
    storage_tips: list[str] = []
    shopping_advice: str = ""


class ProductInfo(BaseModel):
    name: str
    confidence: Optional[float] = None
    bbox: Optional[BBox] = None


class AnalyzeResponse(BaseModel):
    product: ProductInfo
    damage: DamageInfo
    dates: DatesInfo
    ai: Optional[AIInfo] = None
    meta: dict[str, Any] = {}
    message: Optional[str] = None
