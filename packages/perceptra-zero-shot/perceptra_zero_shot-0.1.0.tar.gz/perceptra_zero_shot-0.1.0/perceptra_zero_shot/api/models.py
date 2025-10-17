"""Pydantic models for API request/response."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BoundingBoxResponse(BaseModel):
    """Bounding box response model."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float
    label: str
    label_id: Optional[int] = None


class DetectionRequest(BaseModel):
    """Detection request model."""
    prompts: List[str] = Field(..., description="List of object labels to detect")
    confidence_threshold: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0,
        description="Confidence threshold (0-1)"
    )
    apply_nms: bool = Field(True, description="Apply Non-Maximum Suppression")
    nms_threshold: float = Field(0.5, ge=0.0, le=1.0, description="NMS IoU threshold")
    model_name: Optional[str] = Field(None, description="Model to use for detection")


class DetectionResponse(BaseModel):
    """Detection response model."""
    boxes: List[BoundingBoxResponse]
    num_detections: int
    image_size: Optional[tuple] = None
    model_name: str
    inference_time: float
    metadata: Dict[str, Any] = {}


class ModelInfo(BaseModel):
    """Model information."""
    name: str
    available: bool
    description: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    models_loaded: List[str]