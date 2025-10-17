"""Main detector interface for zero-shot detection."""

from typing import List, Union, Optional, Dict, Any
from PIL import Image
import time

from perceptra_zero_shot.core.result import DetectionResult
from perceptra_zero_shot.models.base import BaseDetectionModel
from perceptra_zero_shot.models.registry import ModelRegistry


class ZeroShotDetector:
    """
    High-level interface for zero-shot object detection.
    
    This class provides a unified API for working with different
    zero-shot detection models like OWL-ViT v2 and Grounding DINO.
    
    Example:
        >>> detector = ZeroShotDetector("owlv2-base")
        >>> result = detector.detect("image.jpg", ["cat", "dog"])
        >>> print(f"Found {len(result)} objects")
    """
    
    def __init__(
        self,
        model_name: str = "owlv2-base",
        device: Optional[str] = None,
        confidence_threshold: float = 0.3,
        **model_kwargs
    ):
        """
        Initialize the zero-shot detector.
        
        Args:
            model_name: Name of the model to use (e.g., 'owlv2-base', 'grounding-dino')
            device: Device to run inference on ('cuda', 'cpu', or None for auto)
            confidence_threshold: Minimum confidence for detections
            **model_kwargs: Additional model-specific parameters
        """
        self.model_name = model_name
        self.model: BaseDetectionModel = ModelRegistry.create(
            model_name=model_name,
            device=device,
            confidence_threshold=confidence_threshold,
            **model_kwargs
        )
        self.model.load_model()
    
    def detect(
        self,
        image: Union[Image.Image, str],
        prompts: Union[str, List[str]],
        confidence_threshold: Optional[float] = None,
        apply_nms: bool = True,
        nms_threshold: float = 0.5,
        **kwargs
    ) -> DetectionResult:
        """
        Detect objects in an image using natural language prompts.
        
        Args:
            image: PIL Image or path to image file
            prompts: Text prompt(s) describing objects to detect.
                    Can be a single string "cat, dog" or list ["cat", "dog"]
            confidence_threshold: Override default confidence threshold
            apply_nms: Whether to apply Non-Maximum Suppression
            nms_threshold: IoU threshold for NMS
            **kwargs: Additional model-specific parameters
        
        Returns:
            DetectionResult containing detected objects
        
        Example:
            >>> detector = ZeroShotDetector("owlv2-base")
            >>> result = detector.detect("image.jpg", ["cat", "dog"])
            >>> for box in result.boxes:
            ...     print(f"{box.label}: {box.confidence:.2f}")
        """
        start_time = time.time()
        
        # Perform detection
        result = self.model.predict(
            image=image,
            prompts=prompts,
            confidence_threshold=confidence_threshold,
            **kwargs
        )
        
        # Apply NMS if requested
        if apply_nms and len(result) > 0:
            result = result.apply_nms(iou_threshold=nms_threshold)
        
        # Update inference time
        result.inference_time = time.time() - start_time
        
        return result
    
    def detect_batch(
        self,
        images: List[Union[Image.Image, str]],
        prompts: Union[str, List[str]],
        confidence_threshold: Optional[float] = None,
        apply_nms: bool = True,
        nms_threshold: float = 0.5,
        **kwargs
    ) -> List[DetectionResult]:
        """
        Detect objects in multiple images.
        
        Args:
            images: List of PIL Images or paths to image files
            prompts: Text prompt(s) describing objects to detect
            confidence_threshold: Override default confidence threshold
            apply_nms: Whether to apply Non-Maximum Suppression
            nms_threshold: IoU threshold for NMS
            **kwargs: Additional model-specific parameters
        
        Returns:
            List of DetectionResults, one per image
        
        Example:
            >>> detector = ZeroShotDetector("owlv2-base")
            >>> results = detector.detect_batch(
            ...     ["img1.jpg", "img2.jpg"],
            ...     ["person", "car"]
            ... )
            >>> for i, result in enumerate(results):
            ...     print(f"Image {i}: {len(result)} detections")
        """
        results = []
        for image in images:
            result = self.detect(
                image=image,
                prompts=prompts,
                confidence_threshold=confidence_threshold,
                apply_nms=apply_nms,
                nms_threshold=nms_threshold,
                **kwargs
            )
            results.append(result)
        return results
    
    def to(self, device: str) -> 'ZeroShotDetector':
        """
        Move model to specified device.
        
        Args:
            device: Device to move to ('cuda' or 'cpu')
            
        Returns:
            Self for method chaining
        """
        self.model.to(device)
        return self
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the detector and model.
        
        Returns:
            Dictionary containing detector metadata
        """
        return {
            "detector_version": "0.1.0",
            "model_info": self.model.get_model_info(),
        }
    
    def __repr__(self) -> str:
        return f"ZeroShotDetector(model={self.model_name}, device={self.model.device})"