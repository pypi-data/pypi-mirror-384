"""Tests for result data structures."""

import pytest
from perceptra_zero_shot.core.result import BoundingBox, DetectionResult


class TestBoundingBox:
    """Tests for BoundingBox class."""
    
    def test_valid_bbox_creation(self):
        """Test creating a valid bounding box."""
        bbox = BoundingBox(
            x_min=10.0,
            y_min=20.0,
            x_max=100.0,
            y_max=200.0,
            confidence=0.85,
            label="cat"
        )
        assert bbox.width == 90.0
        assert bbox.height == 180.0
        assert bbox.area == 16200.0
        assert bbox.center == (55.0, 110.0)
    
    def test_invalid_bbox_coordinates(self):
        """Test that invalid coordinates raise ValueError."""
        with pytest.raises(ValueError):
            BoundingBox(
                x_min=100.0,
                y_min=20.0,
                x_max=10.0,  # x_max < x_min
                y_max=200.0,
                confidence=0.85,
                label="cat"
            )
    
    def test_invalid_confidence(self):
        """Test that invalid confidence raises ValueError."""
        with pytest.raises(ValueError):
            BoundingBox(
                x_min=10.0,
                y_min=20.0,
                x_max=100.0,
                y_max=200.0,
                confidence=1.5,  # > 1.0
                label="cat"
            )
    
    def test_coordinate_formats(self):
        """Test different coordinate format conversions."""
        bbox = BoundingBox(
            x_min=10.0, y_min=20.0,
            x_max=100.0, y_max=200.0,
            confidence=0.85, label="cat"
        )
        
        assert bbox.to_xyxy() == [10.0, 20.0, 100.0, 200.0]
        assert bbox.to_xywh() == [10.0, 20.0, 90.0, 180.0]
        assert bbox.to_cxcywh() == [55.0, 110.0, 90.0, 180.0]
    
    def test_iou_calculation(self):
        """Test IoU calculation between boxes."""
        bbox1 = BoundingBox(0, 0, 100, 100, 0.9, "cat")
        bbox2 = BoundingBox(50, 50, 150, 150, 0.8, "cat")
        
        iou = bbox1.iou(bbox2)
        expected_iou = 2500 / 17500  # intersection / union
        assert abs(iou - expected_iou) < 0.01
    
    def test_no_overlap_iou(self):
        """Test IoU is 0 for non-overlapping boxes."""
        bbox1 = BoundingBox(0, 0, 50, 50, 0.9, "cat")
        bbox2 = BoundingBox(100, 100, 150, 150, 0.8, "dog")
        
        assert bbox1.iou(bbox2) == 0.0


class TestDetectionResult:
    """Tests for DetectionResult class."""
    
    def test_empty_result(self):
        """Test empty detection result."""
        result = DetectionResult()
        assert len(result) == 0
        assert result.get_labels() == []
    
    def test_result_with_boxes(self):
        """Test result with multiple boxes."""
        boxes = [
            BoundingBox(0, 0, 50, 50, 0.9, "cat", 0),
            BoundingBox(100, 100, 150, 150, 0.8, "dog", 1),
            BoundingBox(200, 200, 250, 250, 0.7, "cat", 0),
        ]
        result = DetectionResult(boxes=boxes)
        
        assert len(result) == 3
        assert set(result.get_labels()) == {"cat", "dog"}
    
    def test_filter_by_confidence(self):
        """Test filtering by confidence threshold."""
        boxes = [
            BoundingBox(0, 0, 50, 50, 0.9, "cat"),
            BoundingBox(100, 100, 150, 150, 0.5, "dog"),
            BoundingBox(200, 200, 250, 250, 0.3, "bird"),
        ]
        result = DetectionResult(boxes=boxes)
        
        filtered = result.filter_by_confidence(0.6)
        assert len(filtered) == 1
        assert filtered.boxes[0].label == "cat"
    
    def test_filter_by_label(self):
        """Test filtering by specific labels."""
        boxes = [
            BoundingBox(0, 0, 50, 50, 0.9, "cat"),
            BoundingBox(100, 100, 150, 150, 0.8, "dog"),
            BoundingBox(200, 200, 250, 250, 0.7, "bird"),
        ]
        result = DetectionResult(boxes=boxes)
        
        filtered = result.filter_by_label(["cat", "dog"])
        assert len(filtered) == 2
        assert set(box.label for box in filtered.boxes) == {"cat", "dog"}
    
    def test_nms(self):
        """Test Non-Maximum Suppression."""
        boxes = [
            BoundingBox(0, 0, 100, 100, 0.9, "cat"),
            BoundingBox(10, 10, 110, 110, 0.8, "cat"),  # Overlaps with first
            BoundingBox(200, 200, 300, 300, 0.7, "dog"),
        ]
        result = DetectionResult(boxes=boxes)
        
        nms_result = result.apply_nms(iou_threshold=0.5)
        assert len(nms_result) == 2  # Should keep highest conf cat + dog
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        boxes = [BoundingBox(0, 0, 50, 50, 0.9, "cat")]
        result = DetectionResult(
            boxes=boxes,
            image_size=(640, 480),
            model_name="owlv2-base"
        )
        
        data = result.to_dict()
        assert data["num_detections"] == 1
        assert data["image_size"] == (640, 480)
        assert data["model_name"] == "owlv2-base"
    
    def test_to_coco_format(self):
        """Test conversion to COCO format."""
        boxes = [BoundingBox(10, 20, 100, 200, 0.9, "cat", 0)]
        result = DetectionResult(boxes=boxes)
        
        coco = result.to_coco_format()
        assert len(coco) == 1
        assert coco[0]["bbox"] == [10.0, 20.0, 90.0, 180.0]  # xywh
        assert coco[0]["score"] == 0.9

