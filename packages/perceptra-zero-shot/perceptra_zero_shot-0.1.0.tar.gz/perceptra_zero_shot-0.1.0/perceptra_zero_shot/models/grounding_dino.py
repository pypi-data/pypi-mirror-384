"""Grounding DINO model implementation."""

from typing import List, Union, Optional
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

from perceptra_zero_shot.models.base import BaseDetectionModel
from perceptra_zero_shot.core.result import DetectionResult, BoundingBox
from perceptra_zero_shot.models.registry import ModelRegistry


class GroundingDINOModel(BaseDetectionModel):
    """
    Grounding DINO zero-shot object detection model.
    
    Grounding DINO combines DINO (a transformer-based detector) with
    language grounding capabilities for open-vocabulary detection.
    """
    
    MODEL_CONFIGS = {
        "grounding-dino": "IDEA-Research/grounding-dino-base",
        "grounding-dino-tiny": "IDEA-Research/grounding-dino-tiny",
    }
    
    def __init__(
        self,
        model_name: str = "grounding-dino",
        device: Optional[str] = None,
        confidence_threshold: float = 0.3,
        box_threshold: float = 0.25,
        text_threshold: float = 0.25,
        **kwargs
    ):
        """
        Initialize Grounding DINO model.
        
        Args:
            model_name: Model variant ('grounding-dino' or 'grounding-dino-tiny')
            device: Device to run on
            confidence_threshold: Detection confidence threshold
            box_threshold: Box confidence threshold
            text_threshold: Text-image similarity threshold
            **kwargs: Additional parameters
        """
        super().__init__(model_name, device, confidence_threshold, **kwargs)
        
        if model_name not in self.MODEL_CONFIGS:
            raise ValueError(
                f"Unknown Grounding DINO model: {model_name}. "
                f"Available: {list(self.MODEL_CONFIGS.keys())}"
            )
        
        self.hf_model_name = self.MODEL_CONFIGS[model_name]
        self.box_threshold = box_threshold
        self.text_threshold = text_threshold
    
    def load_model(self) -> None:
        """Load Grounding DINO model and processor from HuggingFace."""
        try:
            print(f"Loading {self.model_name} from {self.hf_model_name}...")
            self.processor = AutoProcessor.from_pretrained(self.hf_model_name)
            self.model = AutoModelForZeroShotObjectDetection.from_pretrained(
                self.hf_model_name
            )
            self.model = self.model.to(self.device)
            self.model.eval()
            self._is_loaded = True
            print(f"Model loaded successfully on {self.device}")
        except Exception as e:
            raise RuntimeError(f"Failed to load Grounding DINO model: {e}")
    
    def predict(
        self,
        image: Union[Image.Image, str],
        prompts: Union[str, List[str]],
        confidence_threshold: Optional[float] = None,
        box_threshold: Optional[float] = None,
        text_threshold: Optional[float] = None,
        **kwargs
    ) -> DetectionResult:
        """
        Perform zero-shot detection using Grounding DINO.
        
        Args:
            image: PIL Image or path to image file
            prompts: Text prompt(s) describing objects to detect
            confidence_threshold: Override default confidence threshold
            box_threshold: Box confidence threshold
            text_threshold: Text-image similarity threshold
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
        box_thresh = box_threshold or self.box_threshold
        text_thresh = text_threshold or self.text_threshold
        
        # Grounding DINO expects prompts in a specific format
        text_prompt = ". ".join(prompts) + "."
        
        # Prepare inputs
        inputs = self.processor(
            images=image,
            text=text_prompt,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Perform inference
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Post-process results
        target_sizes = torch.tensor([image.size[::-1]]).to(self.device)
        results = self.processor.post_process_grounded_object_detection(
            outputs=outputs,
            input_ids=inputs["input_ids"],
            threshold=box_thresh,
            target_sizes=target_sizes
        )[0]
        
        # Convert to BoundingBox objects
        boxes = []
        for box, score, label in zip(
            results["boxes"].cpu().numpy(),
            results["scores"].cpu().numpy(),
            results["labels"]
        ):
            # Match label to original prompt
            matched_prompt = self._match_label_to_prompt(label, prompts)
            
            if score >= threshold:
                boxes.append(BoundingBox(
                    x_min=float(box[0]),
                    y_min=float(box[1]),
                    x_max=float(box[2]),
                    y_max=float(box[3]),
                    confidence=float(score),
                    label=matched_prompt,
                    label_id=prompts.index(matched_prompt) if matched_prompt in prompts else None
                ))
        
        return DetectionResult(
            boxes=boxes,
            image_size=image.size,
            model_name=self.model_name,
            metadata={
                "prompts": prompts,
                "box_threshold": box_thresh,
                "text_threshold": text_thresh
            }
        )
    
    def _match_label_to_prompt(self, label: str, prompts: List[str]) -> str:
        """
        Match detected label to original prompt.
        
        Args:
            label: Detected label from model
            prompts: Original input prompts
            
        Returns:
            Best matching prompt or the label itself
        """
        label_lower = label.lower().strip()
        
        # Direct match
        for prompt in prompts:
            if prompt.lower().strip() == label_lower:
                return prompt
        
        # Partial match
        for prompt in prompts:
            if label_lower in prompt.lower() or prompt.lower() in label_lower:
                return prompt
        
        # Return label as-is if no match
        return label


# Register Grounding DINO models
ModelRegistry.register("grounding-dino", GroundingDINOModel)
ModelRegistry.register("grounding-dino-tiny", GroundingDINOModel)