# Perceptra Zero-Shot

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready toolkit for **zero-shot object detection and segmentation** using state-of-the-art vision-language models.

## 🚀 Features

- **Unified Interface**: Single API for multiple zero-shot detection models
- **Multiple Models**: OWL-ViT v2, Grounding DINO, and extensible architecture
- **Production Ready**: Robust error handling, type hints, comprehensive docs
- **Three Ways to Use**:
  - 🐍 Python Package
  - 🖥️ Command Line Interface (CLI)
  - 🌐 REST API Server
- **Flexible Output**: Dict, COCO format, custom serialization
- **Visualization Tools**: Built-in result visualization
- **Batch Processing**: Efficient multi-image inference

## 📦 Installation

### Basic Installation
```bash
pip install perceptra-zero-shot
```

### With Optional Dependencies
```bash
# For CLI support
pip install perceptra-zero-shot[cli]

# For API server
pip install perceptra-zero-shot[api]

# For visualization
pip install perceptra-zero-shot[viz]

# Install everything
pip install perceptra-zero-shot[all]
```

### From Source
```bash
git clone https://github.com/tannousgeagea/perceptra-zero-shot.git
cd perceptra-zero-shot
pip install -e .
```

## 🎯 Quick Start

### Python Package

```python
from perceptra_zero_shot import ZeroShotDetector
from PIL import Image

# Initialize detector
detector = ZeroShotDetector(model_name="owlv2-base", device="cuda")

# Load image
image = Image.open("photo.jpg")

# Detect objects
result = detector.detect(
    image=image,
    prompts=["cat", "dog", "person"],
    confidence_threshold=0.3
)

# Print results
print(f"Found {len(result)} objects")
for box in result.boxes:
    print(f"{box.label}: {box.confidence:.2f} at {box.to_xyxy()}")
```

### Command Line Interface

```bash
# Detect objects in an image
perceptra detect image.jpg person car dog --model owlv2-base --output result.jpg

# Batch process a directory
perceptra detect-batch images/ person car --pattern "*.jpg" --output-dir results/

# List available models
perceptra list-models

# Start API server
perceptra serve --port 8000
```

### REST API

Start the server:
```bash
perceptra serve --port 8000
```

Use the API:
```python
import requests

url = "http://localhost:8000/detect"
files = {"file": open("image.jpg", "rb")}
data = {"prompts": "person,car,dog"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

Or with curl:
```bash
curl -X POST "http://localhost:8000/detect" \
     -F "file=@image.jpg" \
     -F "prompts=person,car,dog"
```

API Documentation available at: `http://localhost:8000/docs`

## 🤖 Supported Models

| Model | Name | Description |
|-------|------|-------------|
| OWL-ViT v2 Base | `owlv2-base` | Fast, accurate zero-shot detection |
| OWL-ViT v2 Large | `owlv2-large` | Higher accuracy, slower |
| Grounding DINO | `grounding-dino` | State-of-the-art open-vocabulary |
| Grounding DINO Tiny | `grounding-dino-tiny` | Faster, lightweight |

```python
from perceptra_zero_shot import ModelRegistry

# List all available models
print(ModelRegistry.list_models())
```

## 📖 Advanced Usage

### Batch Processing

```python
from perceptra_zero_shot import ZeroShotDetector

detector = ZeroShotDetector("owlv2-base")

# Process multiple images
results = detector.detect_batch(
    images=["img1.jpg", "img2.jpg", "img3.jpg"],
    prompts=["car", "truck", "bus"]
)

for i, result in enumerate(results):
    print(f"Image {i}: {len(result)} detections")
```

### Filtering and Post-Processing

```python
# Filter by confidence
high_conf = result.filter_by_confidence(0.5)

# Filter by specific labels
cars_only = result.filter_by_label(["car"])

# Apply Non-Maximum Suppression
result_nms = result.apply_nms(iou_threshold=0.5)

# Get boxes for specific label
car_boxes = result.get_boxes_by_label("car")
```

### Visualization

```python
from perceptra_zero_shot.utils import visualize_detections

# Visualize results
vis_image = visualize_detections(
    image=image,
    result=result,
    show_labels=True,
    show_confidence=True,
    output_path="output.jpg"
)
```

### Export Formats

```python
# Export as dictionary
data = result.to_dict()

# Export as COCO format
coco_annotations = result.to_coco_format()

# Individual box formats
for box in result.boxes:
    xyxy = box.to_xyxy()      # [x_min, y_min, x_max, y_max]
    xywh = box.to_xywh()      # [x_min, y_min, width, height]
    cxcywh = box.to_cxcywh()  # [center_x, center_y, width, height]
```

### Custom Model Parameters

```python
# OWLv2 with custom settings
detector = ZeroShotDetector(
    model_name="owlv2-base",
    confidence_threshold=0.4,
    device="cuda"
)

# Grounding DINO with custom thresholds
detector = ZeroShotDetector(
    model_name="grounding-dino",
    confidence_threshold=0.3,
    box_threshold=0.25,
    text_threshold=0.25
)
```

## 🏗️ Architecture

```
perceptra-zero-shot/
├── perceptra_zero_shot/
│   ├── core/              # Core detection logic
│   │   ├── detector.py    # Main ZeroShotDetector class
│   │   └── result.py      # DetectionResult & BoundingBox
│   ├── models/            # Model implementations
│   │   ├── base.py        # Abstract base class
│   │   ├── registry.py    # Model registry
│   │   ├── owlv2.py      # OWL-ViT v2
│   │   └── grounding_dino.py  # Grounding DINO
│   ├── utils/             # Utility functions
│   ├── api/               # FastAPI REST API
│   └── cli/               # Command-line interface
├── examples/              # Usage examples
└── tests/                 # Unit tests
```

## 📊 API Reference

### ZeroShotDetector

Main interface for zero-shot object detection.

```python
detector = ZeroShotDetector(
    model_name: str = "owlv2-base",
    device: Optional[str] = None,
    confidence_threshold: float = 0.3,
    **model_kwargs
)
```

**Methods:**
- `detect(image, prompts, **kwargs)` → DetectionResult
- `detect_batch(images, prompts, **kwargs)` → List[DetectionResult]
- `to(device)` → ZeroShotDetector

### DetectionResult

Container for detection results.

**Properties:**
- `boxes`: List[BoundingBox]
- `image_size`: tuple
- `model_name`: str
- `inference_time`: float

**Methods:**
- `filter_by_confidence(threshold)` → DetectionResult
- `filter_by_label(labels)` → DetectionResult
- `apply_nms(iou_threshold)` → DetectionResult
- `to_dict()` → dict
- `to_coco_format()` → List[dict]

### BoundingBox

Represents a detected object.

**Properties:**
- `x_min, y_min, x_max, y_max`: float
- `confidence`: float
- `label`: str
- `width, height, area`: float
- `center`: tuple

**Methods:**
- `to_xyxy()` → List[float]
- `to_xywh()` → List[float]
- `to_cxcywh()` → List[float]
- `iou(other)` → float

## 🔧 Development

### Setup Development Environment

```bash
git clone https://github.com/tannousgeagea/perceptra-zero-shot.git
cd perceptra-zero-shot
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v --cov=perceptra_zero_shot
```

### Code Formatting

```bash
black perceptra_zero_shot/
isort perceptra_zero_shot/
flake8 perceptra_zero_shot/
```

## 🎓 Examples

See the `examples/` directory for complete examples:

- `basic_detection.py` - Simple detection example
- `batch_processing.py` - Process multiple images
- `api_usage.py` - Using the REST API
- `compare_models.py` - Compare different models

## 📝 Requirements

- Python ≥ 3.8
- PyTorch ≥ 2.0.0
- Transformers ≥ 4.30.0
- PIL/Pillow ≥ 9.0.0
- NumPy ≥ 1.21.0

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OWL-ViT v2 by Google Research
- Grounding DINO by IDEA-Research
- Hugging Face Transformers library

## 📚 Citation

```bibtex
@software{perceptra2025,
  title = {Perceptra Zero-Shot: Production-Ready Zero-Shot Object Detection},
  author = {Perceptra Team},
  year = {2025},
  url = {https://github.com/tannousgeagea/perceptra-zero-shot}
}
```

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/tannousgeagea/perceptra-zero-shot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tannousgeagea/perceptra-zero-shot/discussions)
- **Email**: team@perceptra.ai

---

Made with ❤️ by the Perceptra Team