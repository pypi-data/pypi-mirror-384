
"""
Perceptra Zero-Shot: Production-ready zero-shot object detection toolkit.

This package provides a unified interface for zero-shot object detection
using state-of-the-art vision-language models like OWL-ViT v2 and Grounding DINO.
"""

from perceptra_zero_shot.__version__ import __version__, __author__, __email__
from perceptra_zero_shot.core.detector import ZeroShotDetector
from perceptra_zero_shot.core.result import DetectionResult, BoundingBox
from perceptra_zero_shot.models.registry import ModelRegistry

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "ZeroShotDetector",
    "DetectionResult",
    "BoundingBox",
    "ModelRegistry",
]
