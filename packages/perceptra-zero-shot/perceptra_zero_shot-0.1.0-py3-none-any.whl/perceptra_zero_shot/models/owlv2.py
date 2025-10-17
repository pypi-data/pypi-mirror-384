"""OWL-ViT v2 model implementation."""

from typing import List, Union, Optional
from PIL import Image
import torch
from transformers import Owlv2Processor, Owlv2ForObjectDetection

from perceptra_zero_shot.models.base import BaseDetectionModel
from perceptra_zero_shot.core.result import DetectionResult, BoundingBox
from perceptra_zero_shot.models.registry import ModelRegistry

class OWLv2Model(BaseDetectionModel):
    """
    OWL-ViT v2 zero-shot object detection model.
    
    OWL-ViT (Open-World Localization Vision Transformer) is a zero-shot
    object detection model that can detect objects based on text descriptions.
    """
    
    MODEL_CONFIGS = {
        "owlv2-base": "google/owlv2-base-patch16-ensemble",
        "owlv2-large": "google/owlv2-large-patch14-ensemble",
        "owlv2-base-patch16": "google/owlv2-base-patch16",
        "owlv2-large-patch14": "google/owlv2-large-patch14",
    }
    
    def __init__(
        self,
        model_name: str = "owlv2-base",
        device: Optional[str] = None,
        confidence_threshold: float = 0.3,
        **kwargs
    ):
        """
        Initialize OWL-ViT v2 model.
        
        Args:
            model_name: Model variant ('owlv2-base' or 'owlv2-large')
            device: Device to run on
            confidence_threshold: Detection confidence threshold
            **kwargs: Additional parameters
        
        Returns:
            DetectionResult containing detected objects
        """
        super().__init__(model_name, device, confidence_threshold, **kwargs)
        
        if model_name not in self.MODEL_CONFIGS:
            raise ValueError(
                f"Unknown OWLv2 model: {model_name}. "
                f"Available: {list(self.MODEL_CONFIGS.keys())}"
            )
        
        self.hf_model_name = self.MODEL_CONFIGS[model_name]
    
    def load_model(self) -> None:
        """Load OWL-ViT v2 model and processor."""
        try:
            self.processor = Owlv2Processor.from_pretrained(self.hf_model_name)
            self.model = Owlv2ForObjectDetection.from_pretrained(self.hf_model_name)
            self.model = self.model.to(self.device)
            self.model.eval()
            self._is_loaded = True
        except Exception as e:
            raise RuntimeError(f"Failed to load OWLv2 model: {e}")
    
    def predict(
        self,
        image: Union[Image.Image, str],
        prompts: Union[str, List[str]],
        confidence_threshold: Optional[float] = None,
        **kwargs
    ) -> DetectionResult:
        """
        Perform zero-shot detection using OWL-ViT v2.
        
        Args:
            image: PIL Image or path to image file
            prompts: Text prompt(s) describing objects to detect
            confidence_threshold: Override default confidence threshold
            **kwargs: Additional parameters
        
        Returns:
            DetectionResult containing detected objects
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Load and normalize inputs
        image = self._load_image(image)
        prompts = self._normalize_prompts(prompts)
        threshold = confidence_threshold or self.confidence_threshold
        
        # Prepare inputs
        inputs = self.processor(
            text=prompts,
            images=image,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Perform inference
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Post-process results
        target_sizes = torch.tensor([image.size[::-1]]).to(self.device)
        results = self.processor.post_process_object_detection(
            outputs=outputs,
            target_sizes=target_sizes,
            threshold=threshold
        )[0]
        
        # Convert to BoundingBox objects
        boxes = []
        for box, score, label in zip(
            results["boxes"].cpu().numpy(),
            results["scores"].cpu().numpy(),
            results["labels"].cpu().numpy()
        ):
            boxes.append(BoundingBox(
                x_min=float(box[0]),
                y_min=float(box[1]),
                x_max=float(box[2]),
                y_max=float(box[3]),
                confidence=float(score),
                label=prompts[label],
                label_id=int(label)
            ))
        
        return DetectionResult(
            boxes=boxes,
            image_size=image.size,
            model_name=self.model_name,
            metadata={"prompts": prompts}
        )

# Register OWLv2 models
ModelRegistry.register("owlv2-base", OWLv2Model)
ModelRegistry.register("owlv2-large", OWLv2Model)
ModelRegistry.register("owlv2-base-patch16", OWLv2Model)
ModelRegistry.register("owlv2-large-patch14", OWLv2Model)