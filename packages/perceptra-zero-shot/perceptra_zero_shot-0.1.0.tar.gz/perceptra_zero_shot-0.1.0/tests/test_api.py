"""Tests for REST API."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from PIL import Image
import io

from perceptra_zero_shot.api import app
from perceptra_zero_shot.core.result import DetectionResult, BoundingBox


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_image_file():
    """Create a mock image file."""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


class TestAPI:
    """Tests for REST API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "version" in response.json()
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_list_models_endpoint(self, client):
        """Test list models endpoint."""
        response = client.get("/models")
        assert response.status_code == 200
        models = response.json()
        assert len(models) > 0
        assert all("name" in m for m in models)
    
    @patch('perceptra_zero_shot.api.main.get_detector')
    def test_detect_endpoint(self, mock_get_detector, client, mock_image_file):
        """Test detection endpoint."""
        # Setup mock detector
        mock_detector = Mock()
        mock_result = DetectionResult(
            boxes=[BoundingBox(10, 20, 100, 200, 0.9, "cat", 0)],
            image_size=(100, 100),
            model_name="owlv2-base",
            inference_time=0.5
        )
        mock_detector.detect.return_value = mock_result
        mock_get_detector.return_value = mock_detector
        
        # Make request
        response = client.post(
            "/detect",
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
            data={"prompts": "cat,dog"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["num_detections"] == 1
        assert data["boxes"][0]["label"] == "cat"