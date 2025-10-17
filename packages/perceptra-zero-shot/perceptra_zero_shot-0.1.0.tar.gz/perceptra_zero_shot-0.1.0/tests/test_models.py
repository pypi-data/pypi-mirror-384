"""Tests for model implementations."""

import pytest
from perceptra_zero_shot.models.registry import ModelRegistry
from perceptra_zero_shot.models.base import BaseDetectionModel


class TestModelRegistry:
    """Tests for ModelRegistry."""
    
    def test_list_models(self):
        """Test listing available models."""
        models = ModelRegistry.list_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "owlv2-base" in models
    
    def test_is_registered(self):
        """Test checking if model is registered."""
        assert ModelRegistry.is_registered("owlv2-base")
        assert not ModelRegistry.is_registered("nonexistent-model")
    
    def test_create_invalid_model(self):
        """Test creating non-existent model raises error."""
        with pytest.raises(ValueError, match="not found"):
            ModelRegistry.create("nonexistent-model")
    
    def test_get_model_info(self):
        """Test getting model information."""
        info = ModelRegistry.get_model_info()
        assert isinstance(info, dict)
        assert "owlv2-base" in info


class TestBaseDetectionModel:
    """Tests for BaseDetectionModel."""
    
    def test_normalize_prompts_string(self):
        """Test prompt normalization from string."""
        class DummyModel(BaseDetectionModel):
            def load_model(self): pass
            def predict(self, *args, **kwargs): pass
        
        model = DummyModel("test", device="cpu")
        
        # Test comma-separated
        prompts = model._normalize_prompts("cat, dog, bird")
        assert prompts == ["cat", "dog", "bird"]
        
        # Test single prompt
        prompts = model._normalize_prompts("cat")
        assert prompts == ["cat"]
    
    def test_normalize_prompts_list(self):
        """Test prompt normalization from list."""
        class DummyModel(BaseDetectionModel):
            def load_model(self): pass
            def predict(self, *args, **kwargs): pass
        
        model = DummyModel("test", device="cpu")
        prompts = model._normalize_prompts(["cat", "dog"])
        assert prompts == ["cat", "dog"]