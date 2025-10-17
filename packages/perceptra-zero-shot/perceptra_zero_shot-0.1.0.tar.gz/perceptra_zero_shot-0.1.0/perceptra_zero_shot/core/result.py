"""Data structures for detection results."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union


@dataclass
class BoundingBox:
    """
    Represents a bounding box with coordinates and metadata.
    
    Attributes:
        x_min: Left x coordinate
        y_min: Top y coordinate
        x_max: Right x coordinate
        y_max: Bottom y coordinate
        confidence: Detection confidence score (0-1)
        label: Object class label
        label_id: Optional numeric label ID
    """
    
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float
    label: str
    label_id: Optional[int] = None
    
    def __post_init__(self):
        """Validate bounding box coordinates and confidence."""
        if self.x_min >= self.x_max or self.y_min >= self.y_max:
            raise ValueError(
                f"Invalid bounding box: ({self.x_min}, {self.y_min}) to "
                f"({self.x_max}, {self.y_max})"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0 and 1, got {self.confidence}"
            )
    
    @property
    def width(self) -> float:
        """Width of the bounding box."""
        return self.x_max - self.x_min
    
    @property
    def height(self) -> float:
        """Height of the bounding box."""
        return self.y_max - self.y_min
    
    @property
    def area(self) -> float:
        """Area of the bounding box."""
        return self.width * self.height
    
    @property
    def center(self) -> tuple:
        """Center point (x, y) of the bounding box."""
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)
    
    def to_xyxy(self) -> List[float]:
        """Return coordinates in [x_min, y_min, x_max, y_max] format."""
        return [self.x_min, self.y_min, self.x_max, self.y_max]
    
    def to_xywh(self) -> List[float]:
        """Return coordinates in [x_min, y_min, width, height] format."""
        return [self.x_min, self.y_min, self.width, self.height]
    
    def to_cxcywh(self) -> List[float]:
        """Return coordinates in [center_x, center_y, width, height] format."""
        cx, cy = self.center
        return [cx, cy, self.width, self.height]
    
    def iou(self, other: 'BoundingBox') -> float:
        """
        Calculate Intersection over Union with another bounding box.
        
        Args:
            other: Another BoundingBox to compare with
            
        Returns:
            IoU score (0-1)
        """
        x_left = max(self.x_min, other.x_min)
        y_top = max(self.y_min, other.y_min)
        x_right = min(self.x_max, other.x_max)
        y_bottom = min(self.y_max, other.y_max)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        union = self.area + other.area - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "bbox": self.to_xyxy(),
            "confidence": self.confidence,
            "label": self.label,
            "label_id": self.label_id,
        }


@dataclass
class DetectionResult:
    """
    Container for detection results from a zero-shot model.
    
    Attributes:
        boxes: List of detected bounding boxes
        image_size: Original image dimensions (width, height)
        model_name: Name of the model used for detection
        inference_time: Time taken for inference in seconds
        metadata: Additional metadata dictionary
    """
    
    boxes: List[BoundingBox] = field(default_factory=list)
    image_size: Optional[tuple] = None
    model_name: Optional[str] = None
    inference_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        """Number of detected objects."""
        return len(self.boxes)
    
    def __iter__(self):
        """Iterate over bounding boxes."""
        return iter(self.boxes)
    
    def __getitem__(self, index: Union[int, slice]) -> Union[BoundingBox, List[BoundingBox]]:
        """Get box by index or slice."""
        return self.boxes[index]
    
    def filter_by_confidence(self, threshold: float) -> 'DetectionResult':
        """
        Filter detections by confidence threshold.
        
        Args:
            threshold: Minimum confidence score
            
        Returns:
            New DetectionResult with filtered boxes
        """
        filtered_boxes = [box for box in self.boxes if box.confidence >= threshold]
        return DetectionResult(
            boxes=filtered_boxes,
            image_size=self.image_size,
            model_name=self.model_name,
            inference_time=self.inference_time,
            metadata=self.metadata.copy(),
        )
    
    def filter_by_label(self, labels: List[str]) -> 'DetectionResult':
        """
        Filter detections by specific labels.
        
        Args:
            labels: List of labels to keep
            
        Returns:
            New DetectionResult with filtered boxes
        """
        label_set = set(labels)
        filtered_boxes = [box for box in self.boxes if box.label in label_set]
        return DetectionResult(
            boxes=filtered_boxes,
            image_size=self.image_size,
            model_name=self.model_name,
            inference_time=self.inference_time,
            metadata=self.metadata.copy(),
        )
    
    def apply_nms(self, iou_threshold: float = 0.5) -> 'DetectionResult':
        """
        Apply Non-Maximum Suppression to remove overlapping boxes.
        
        Args:
            iou_threshold: IoU threshold for suppression
            
        Returns:
            New DetectionResult with NMS applied
        """
        if not self.boxes:
            return self
        
        # Sort by confidence (descending)
        sorted_boxes = sorted(self.boxes, key=lambda b: b.confidence, reverse=True)
        keep_boxes = []
        
        while sorted_boxes:
            current = sorted_boxes.pop(0)
            keep_boxes.append(current)
            
            # Remove boxes with high IoU with current box and same label
            sorted_boxes = [
                box for box in sorted_boxes
                if current.iou(box) < iou_threshold or box.label != current.label
            ]
        
        return DetectionResult(
            boxes=keep_boxes,
            image_size=self.image_size,
            model_name=self.model_name,
            inference_time=self.inference_time,
            metadata=self.metadata.copy(),
        )
    
    def get_labels(self) -> List[str]:
        """Get unique labels from detections."""
        return list(set(box.label for box in self.boxes))
    
    def get_boxes_by_label(self, label: str) -> List[BoundingBox]:
        """
        Get all boxes for a specific label.
        
        Args:
            label: Label to filter by
            
        Returns:
            List of BoundingBoxes with the specified label
        """
        return [box for box in self.boxes if box.label == label]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "detections": [box.to_dict() for box in self.boxes],
            "num_detections": len(self.boxes),
            "image_size": self.image_size,
            "model_name": self.model_name,
            "inference_time": self.inference_time,
            "metadata": self.metadata,
        }
    
    def to_coco_format(self) -> List[Dict[str, Any]]:
        """
        Convert to COCO annotation format.
        
        Returns:
            List of annotations in COCO format
        """
        annotations = []
        for idx, box in enumerate(self.boxes):
            annotations.append({
                "id": idx,
                "bbox": box.to_xywh(),
                "category_id": box.label_id if box.label_id is not None else 0,
                "category_name": box.label,
                "score": box.confidence,
                "area": box.area,
            })
        return annotations