"""Abstract base class for detection models."""

from abc import ABC, abstractmethod
from typing import List, Union, Optional, Dict, Any
from PIL import Image
import torch

from perceptra_zero_shot.core.result import DetectionResult


class BaseDetectionModel(ABC):
    """
    Abstract base class for all zero-shot detection models.
    
    All model implementations must inherit from this class and implement
    the abstract methods.
    """
    
    def __init__(
        self,
        model_name: str,
        device: Optional[str] = None,
        confidence_threshold: float = 0.3,
        **kwargs
    ):
        """
        Initialize the detection model.
        
        Args:
            model_name: Name/identifier of the model
            device: Device to run inference on ('cuda', 'cpu', or None for auto)
            confidence_threshold: Minimum confidence for detections
            **kwargs: Additional model-specific parameters
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.device = self._setup_device(device)
        self.model = None
        self.processor = None
        self._is_loaded = False
        self.config = kwargs
    
    def _setup_device(self, device: Optional[str]) -> torch.device:
        """
        Setup the computation device.
        
        Args:
            device: Device string or None for auto-detection
            
        Returns:
            torch.device object
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        return torch.device(device)
    
    @abstractmethod
    def load_model(self) -> None:
        """
        Load the model weights and processors.
        
        This method must be implemented by each model class to load
        the specific model architecture and preprocessing components.
        """
        pass
    
    @abstractmethod
    def predict(
        self,
        image: Union[Image.Image, str],
        prompts: Union[str, List[str]],
        confidence_threshold: Optional[float] = None,
        **kwargs
    ) -> DetectionResult:
        """
        Perform zero-shot detection on an image.
        
        Args:
            image: PIL Image or path to image file
            prompts: Text prompt(s) describing objects to detect
            confidence_threshold: Override default confidence threshold
            **kwargs: Additional inference parameters
        
        Returns:
            DetectionResult containing detected objects
        """
        pass
    
    def _load_image(self, image: Union[Image.Image, str]) -> Image.Image:
        """
        Load and validate image input.
        
        Args:
            image: PIL Image or path to image file
            
        Returns:
            PIL Image in RGB mode
            
        Raises:
            ValueError: If image cannot be loaded
            TypeError: If image type is invalid
        """
        if isinstance(image, str):
            try:
                image = Image.open(image).convert("RGB")
            except Exception as e:
                raise ValueError(f"Failed to load image from {image}: {e}")
        elif not isinstance(image, Image.Image):
            raise TypeError(
                f"Expected PIL Image or path string, got {type(image)}"
            )
        
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        return image
    
    def _normalize_prompts(self, prompts: Union[str, List[str]]) -> List[str]:
        """
        Normalize prompt input to list format.
        
        Args:
            prompts: Single string or list of strings
            
        Returns:
            List of prompt strings
        """
        if isinstance(prompts, str):
            # Split by common delimiters
            if "," in prompts:
                prompts = [p.strip() for p in prompts.split(",")]
            elif ";" in prompts:
                prompts = [p.strip() for p in prompts.split(";")]
            else:
                prompts = [prompts.strip()]
        return [p for p in prompts if p]  # Remove empty strings
    
    def __call__(self, *args, **kwargs) -> DetectionResult:
        """Allow model to be called directly."""
        return self.predict(*args, **kwargs)
    
    def to(self, device: Union[str, torch.device]) -> 'BaseDetectionModel':
        """
        Move model to specified device.
        
        Args:
            device: Device to move to
            
        Returns:
            Self for method chaining
        """
        self.device = torch.device(device) if isinstance(device, str) else device
        if self.model is not None:
            self.model = self.model.to(self.device)
        return self
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary containing model metadata
        """
        return {
            "model_name": self.model_name,
            "device": str(self.device),
            "confidence_threshold": self.confidence_threshold,
            "is_loaded": self._is_loaded,
            "config": self.config,
        }