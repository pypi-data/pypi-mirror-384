"""Tests for ZeroShotDetector."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np

from perceptra_zero_shot import ZeroShotDetector
from perceptra_zero_shot.core.result import DetectionResult, BoundingBox


class TestZeroShotDetector:
    """Tests for ZeroShotDetector class."""
    
    @pytest.fixture
    def mock_image(self):
        """Create a mock PIL Image."""
        return Image.new('RGB', (640, 480), color='red')
    
    @patch('perceptra_zero_shot.models.registry.ModelRegistry.create')
    def test_detector_initialization(self, mock_create):
        """Test detector initialization."""
        mock_model = Mock()
        mock_create.return_value = mock_model
        
        detector = ZeroShotDetector(model_name="owlv2-base", device="cpu")
        
        mock_create.assert_called_once()
        mock_model.load_model.assert_called_once()
    
    @patch('perceptra_zero_shot.models.registry.ModelRegistry.create')
    def test_detect_single_image(self, mock_create, mock_image):
        """Test detection on a single image."""
        # Setup mock model
        mock_model = Mock()
        mock_result = DetectionResult(
            boxes=[BoundingBox(10, 20, 100, 200, 0.9, "cat")],
            image_size=(640, 480)
        )
        mock_model.predict.return_value = mock_result
        mock_create.return_value = mock_model
        
        # Create detector and detect
        detector = ZeroShotDetector(model_name="owlv2-base")
        result = detector.detect(mock_image, ["cat", "dog"])
        
        assert len(result) == 1
        assert result.boxes[0].label == "cat"
        assert result.inference_time is not None
    
    @patch('perceptra_zero_shot.models.registry.ModelRegistry.create')
    def test_detect_batch(self, mock_create, mock_image):
        """Test batch detection."""
        mock_model = Mock()
        mock_result = DetectionResult(boxes=[])
        mock_model.predict.return_value = mock_result
        mock_create.return_value = mock_model
        
        detector = ZeroShotDetector(model_name="owlv2-base")
        results = detector.detect_batch([mock_image, mock_image], ["cat"])
        
        assert len(results) == 2
        assert all(isinstance(r, DetectionResult) for r in results)