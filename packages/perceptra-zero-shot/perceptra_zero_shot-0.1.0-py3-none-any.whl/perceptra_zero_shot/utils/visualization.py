"""Visualization utilities for detection results."""

from typing import Optional, Tuple, List, Dict
from PIL import Image, ImageDraw, ImageFont
import random

from perceptra_zero_shot.core.result import DetectionResult, BoundingBox


def get_color_palette(num_colors: int, seed: int = 42) -> List[Tuple[int, int, int]]:
    """
    Generate a color palette for visualization.
    
    Args:
        num_colors: Number of colors to generate
        seed: Random seed for reproducibility
        
    Returns:
        List of RGB color tuples
    """
    random.seed(seed)
    colors = []
    for _ in range(num_colors):
        colors.append((
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        ))
    return colors


def draw_boxes(
    image: Image.Image,
    result: DetectionResult,
    show_labels: bool = True,
    show_confidence: bool = True,
    box_width: int = 3,
    font_size: int = 16,
    color_map: Optional[Dict[str, Tuple[int, int, int]]] = None
) -> Image.Image:
    """
    Draw bounding boxes on an image.
    
    Args:
        image: PIL Image to draw on
        result: DetectionResult containing boxes to draw
        show_labels: Whether to show label text
        show_confidence: Whether to show confidence scores
        box_width: Width of bounding box lines
        font_size: Size of label font
        color_map: Optional mapping of labels to RGB colors
    
    Returns:
        New image with drawn bounding boxes
    """
    # Create a copy to avoid modifying original
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
    
    # Generate colors for each unique label
    if color_map is None:
        unique_labels = result.get_labels()
        colors = get_color_palette(len(unique_labels))
        color_map = {label: colors[i] for i, label in enumerate(unique_labels)}
    
    # Draw each box
    for box in result.boxes:
        color = color_map.get(box.label, (0, 255, 0))
        
        # Draw rectangle
        draw.rectangle(
            [box.x_min, box.y_min, box.x_max, box.y_max],
            outline=color,
            width=box_width
        )
        
        # Draw label and confidence
        if show_labels or show_confidence:
            label_parts = []
            if show_labels:
                label_parts.append(box.label)
            if show_confidence:
                label_parts.append(f"{box.confidence:.2f}")
            
            label_text = " ".join(label_parts)
            
            # Draw text background
            bbox = draw.textbbox((box.x_min, box.y_min - font_size - 4), label_text, font=font)
            draw.rectangle(bbox, fill=color)
            
            # Draw text
            draw.text(
                (box.x_min + 2, box.y_min - font_size - 2),
                label_text,
                fill=(255, 255, 255),
                font=font
            )
    
    return img_copy


def visualize_detections(
    image: Image.Image,
    result: DetectionResult,
    output_path: Optional[str] = None,
    **kwargs
) -> Image.Image:
    """
    Visualize detection results on an image.
    
    Args:
        image: PIL Image to visualize
        result: DetectionResult containing detections
        output_path: Optional path to save the visualization
        **kwargs: Additional arguments passed to draw_boxes
    
    Returns:
        Image with visualized detections
        
    Example:
        >>> from PIL import Image
        >>> image = Image.open("photo.jpg")
        >>> vis_img = visualize_detections(image, result, "output.jpg")
    """
    vis_image = draw_boxes(image, result, **kwargs)
    
    if output_path:
        vis_image.save(output_path)
        print(f"Visualization saved to {output_path}")
    
    return vis_image
