"""Core detection components."""

from perceptra_zero_shot.core.detector import ZeroShotDetector
from perceptra_zero_shot.core.result import DetectionResult, BoundingBox

__all__ = ["ZeroShotDetector", "DetectionResult", "BoundingBox"]