"""Image processing utilities."""

from typing import List, Union, Tuple, Optional
from PIL import Image
import os


def resize_image(
    image: Image.Image,
    target_size: Union[int, Tuple[int, int]],
    keep_aspect_ratio: bool = True
) -> Image.Image:
    """
    Resize an image to target size.
    
    Args:
        image: PIL Image to resize
        target_size: Target size (int for max dimension, tuple for (width, height))
        keep_aspect_ratio: Whether to maintain aspect ratio
    
    Returns:
        Resized PIL Image
        
    Example:
        >>> img = Image.open("large.jpg")
        >>> resized = resize_image(img, 800)  # Max dimension 800px
    """
    if isinstance(target_size, int):
        if keep_aspect_ratio:
            # Resize to max dimension while keeping aspect ratio
            w, h = image.size
            if w > h:
                new_w = target_size
                new_h = int(h * target_size / w)
            else:
                new_h = target_size
                new_w = int(w * target_size / h)
            target_size = (new_w, new_h)
        else:
            target_size = (target_size, target_size)
    
    return image.resize(target_size, Image.LANCZOS)


def load_image_batch(
    image_paths: List[str],
    target_size: Optional[Union[int, Tuple[int, int]]] = None,
    verify: bool = True
) -> List[Image.Image]:
    """
    Load a batch of images from file paths.
    
    Args:
        image_paths: List of paths to image files
        target_size: Optional target size for resizing
        verify: Whether to verify image files exist
    
    Returns:
        List of PIL Images
        
    Raises:
        FileNotFoundError: If an image file doesn't exist (when verify=True)
        
    Example:
        >>> paths = ["img1.jpg", "img2.jpg", "img3.jpg"]
        >>> images = load_image_batch(paths, target_size=800)
    """
    images = []
    for path in image_paths:
        if verify and not os.path.exists(path):
            raise FileNotFoundError(f"Image not found: {path}")
        
        try:
            img = Image.open(path).convert("RGB")
            
            if target_size is not None:
                img = resize_image(img, target_size)
            
            images.append(img)
        except Exception as e:
            raise RuntimeError(f"Failed to load image {path}: {e}")
    
    return images