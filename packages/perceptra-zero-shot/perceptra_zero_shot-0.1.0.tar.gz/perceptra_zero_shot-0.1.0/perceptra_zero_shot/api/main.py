"""FastAPI application for perceptra-zero-shot."""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List
import io
from PIL import Image
import json

from perceptra_zero_shot import ZeroShotDetector, ModelRegistry, __version__
from perceptra_zero_shot.api.models import (
    DetectionRequest,
    DetectionResponse,
    BoundingBoxResponse,
    ModelInfo,
    HealthResponse
)
from perceptra_zero_shot.utils import visualize_detections

# Create FastAPI app
app = FastAPI(
    title="Perceptra Zero-Shot API",
    description="Production-ready zero-shot object detection REST API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global detector cache
_detector_cache = {}


def get_detector(model_name: str = "owlv2-base") -> ZeroShotDetector:
    """Get or create a detector instance."""
    if model_name not in _detector_cache:
        _detector_cache[model_name] = ZeroShotDetector(model_name=model_name)
    return _detector_cache[model_name]


@app.get("/", tags=["General"])
async def root():
    """Root endpoint."""
    return {
        "message": "Perceptra Zero-Shot API",
        "version": __version__,
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        models_loaded=list(_detector_cache.keys())
    )


@app.get("/models", response_model=List[ModelInfo], tags=["Models"])
async def list_models():
    """List all available models."""
    models = ModelRegistry.list_models()
    return [
        ModelInfo(
            name=model,
            available=True,
            description=f"Zero-shot detection model: {model}"
        )
        for model in models
    ]


@app.post("/detect", response_model=DetectionResponse, tags=["Detection"])
async def detect_objects(
    file: UploadFile = File(..., description="Image file to process"),
    prompts: str = Form(..., description="Comma-separated list of prompts"),
    model_name: Optional[str] = Form("owlv2-base", description="Model to use"),
    confidence_threshold: Optional[float] = Form(0.3, ge=0.0, le=1.0),
    apply_nms: bool = Form(True),
    nms_threshold: float = Form(0.5, ge=0.0, le=1.0)
):
    """
    Detect objects in an uploaded image.
    
    Upload an image and provide comma-separated prompts to detect objects.
    
    Example:
        curl -X POST "http://localhost:8000/detect" \\
             -F "file=@image.jpg" \\
             -F "prompts=person,car,dog"
    """
    try:
        # Read and validate image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Parse prompts
        prompt_list = [p.strip() for p in prompts.split(",") if p.strip()]
        if not prompt_list:
            raise HTTPException(status_code=400, detail="No valid prompts provided")
        
        # Get detector
        detector = get_detector(model_name)
        
        # Perform detection
        result = detector.detect(
            image=image,
            prompts=prompt_list,
            confidence_threshold=confidence_threshold,
            apply_nms=apply_nms,
            nms_threshold=nms_threshold
        )
        
        # Convert to response model
        boxes = [
            BoundingBoxResponse(
                x_min=box.x_min,
                y_min=box.y_min,
                x_max=box.x_max,
                y_max=box.y_max,
                confidence=box.confidence,
                label=box.label,
                label_id=box.label_id
            )
            for box in result.boxes
        ]
        
        return DetectionResponse(
            boxes=boxes,
            num_detections=len(boxes),
            image_size=result.image_size,
            model_name=result.model_name,
            inference_time=result.inference_time,
            metadata=result.metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect/visualize", tags=["Detection"])
async def detect_and_visualize(
    file: UploadFile = File(..., description="Image file to process"),
    prompts: str = Form(..., description="Comma-separated list of prompts"),
    model_name: Optional[str] = Form("owlv2-base"),
    confidence_threshold: Optional[float] = Form(0.3, ge=0.0, le=1.0),
    apply_nms: bool = Form(True),
    nms_threshold: float = Form(0.5, ge=0.0, le=1.0)
):
    """
    Detect objects and return visualized image.
    
    Returns an image with drawn bounding boxes instead of JSON.
    """
    try:
        # Read and validate image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Parse prompts
        prompt_list = [p.strip() for p in prompts.split(",") if p.strip()]
        if not prompt_list:
            raise HTTPException(status_code=400, detail="No valid prompts provided")
        
        # Get detector
        detector = get_detector(model_name)
        
        # Perform detection
        result = detector.detect(
            image=image,
            prompts=prompt_list,
            confidence_threshold=confidence_threshold,
            apply_nms=apply_nms,
            nms_threshold=nms_threshold
        )
        
        # Visualize results
        vis_image = visualize_detections(image, result)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        vis_image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/jpeg")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect/batch", tags=["Detection"])
async def detect_batch(
    files: List[UploadFile] = File(..., description="Multiple image files"),
    prompts: str = Form(..., description="Comma-separated list of prompts"),
    model_name: Optional[str] = Form("owlv2-base"),
    confidence_threshold: Optional[float] = Form(0.3, ge=0.0, le=1.0),
    apply_nms: bool = Form(True),
    nms_threshold: float = Form(0.5, ge=0.0, le=1.0)
):
    """
    Detect objects in multiple images.
    
    Upload multiple images for batch processing.
    """
    try:
        # Parse prompts
        prompt_list = [p.strip() for p in prompts.split(",") if p.strip()]
        if not prompt_list:
            raise HTTPException(status_code=400, detail="No valid prompts provided")
        
        # Get detector
        detector = get_detector(model_name)
        
        # Process each image
        results = []
        for file in files:
            contents = await file.read()
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            
            result = detector.detect(
                image=image,
                prompts=prompt_list,
                confidence_threshold=confidence_threshold,
                apply_nms=apply_nms,
                nms_threshold=nms_threshold
            )
            
            results.append({
                "filename": file.filename,
                "detections": result.to_dict()
            })
        
        return JSONResponse(content={
            "num_images": len(results),
            "results": results
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)