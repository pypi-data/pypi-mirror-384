"""Model registry for managing available detection models."""

from typing import Dict, Type, Optional, List

from perceptra_zero_shot.models.base import BaseDetectionModel


class ModelRegistry:
    """
    Registry for zero-shot detection models.
    
    This class maintains a central registry of all available models
    and provides factory methods for creating model instances.
    """
    
    _models: Dict[str, Type[BaseDetectionModel]] = {}
    
    @classmethod
    def register(cls, name: str, model_class: Type[BaseDetectionModel]) -> None:
        """
        Register a new model class.
        
        Args:
            name: Unique name for the model
            model_class: Model class that inherits from BaseDetectionModel
        """
        cls._models[name] = model_class
    
    @classmethod
    def create(
        cls,
        model_name: str,
        device: Optional[str] = None,
        **kwargs
    ) -> BaseDetectionModel:
        """
        Create an instance of a registered model.
        
        Args:
            model_name: Name of the model to create
            device: Device to run inference on
            **kwargs: Additional model-specific parameters
        
        Returns:
            Instance of the requested model
        
        Raises:
            ValueError: If model_name is not registered
        """
        if model_name not in cls._models:
            available = ", ".join(cls.list_models())
            raise ValueError(
                f"Model '{model_name}' not found. Available models: {available}"
            )
        
        model_class = cls._models[model_name]
        return model_class(
            model_name=model_name,
            device=device,
            **kwargs
        )
    
    @classmethod
    def list_models(cls) -> List[str]:
        """
        List all registered model names.
        
        Returns:
            List of model names
        """
        return list(cls._models.keys())
    
    @classmethod
    def is_registered(cls, model_name: str) -> bool:
        """
        Check if a model is registered.
        
        Args:
            model_name: Name to check
            
        Returns:
            True if registered, False otherwise
        """
        return model_name in cls._models
    
    @classmethod
    def get_model_info(cls) -> Dict[str, Dict[str, str]]:
        """
        Get information about all registered models.
        
        Returns:
            Dictionary mapping model names to their info
        """
        info = {}
        for name, model_class in cls._models.items():
            info[name] = {
                "name": name,
                "class": model_class.__name__,
                "module": model_class.__module__,
            }
        return info
