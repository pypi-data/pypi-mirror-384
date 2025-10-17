"""CLI commands for perceptra-zero-shot."""

import click
from pathlib import Path
from PIL import Image
import json

from perceptra_zero_shot import ZeroShotDetector, ModelRegistry, __version__
from perceptra_zero_shot.utils import visualize_detections


@click.group()
@click.version_option(version=__version__)
def cli():
    """Perceptra Zero-Shot: Production-ready zero-shot object detection toolkit."""
    pass


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.argument('prompts', nargs=-1, required=True)
@click.option('--model', '-m', default='owlv2-base', help='Model to use')
@click.option('--device', '-d', default=None, help='Device (cuda/cpu)')
@click.option('--confidence', '-c', default=0.3, type=float, help='Confidence threshold')
@click.option('--output', '-o', type=click.Path(), help='Output image path')
@click.option('--json-output', '-j', type=click.Path(), help='JSON output path')
@click.option('--no-nms', is_flag=True, help='Disable NMS')
@click.option('--nms-threshold', default=0.5, type=float, help='NMS IoU threshold')
def detect(image_path, prompts, model, device, confidence, output, json_output, no_nms, nms_threshold):
    """
    Detect objects in an image.
    
    Example:
        perceptra detect image.jpg person car dog --model owlv2-base
    """
    click.echo(f"Loading model: {model}")
    detector = ZeroShotDetector(
        model_name=model,
        device=device,
        confidence_threshold=confidence
    )
    
    click.echo(f"Processing: {image_path}")
    click.echo(f"Prompts: {', '.join(prompts)}")
    
    # Load image
    image = Image.open(image_path)
    
    # Perform detection
    result = detector.detect(
        image=image,
        prompts=list(prompts),
        apply_nms=not no_nms,
        nms_threshold=nms_threshold
    )
    
    # Display results
    click.echo(f"\nFound {len(result)} objects in {result.inference_time or 0:.2f}s:")
    for i, box in enumerate(result.boxes, 1):
        click.echo(f"  {i}. {box.label}: {box.confidence:.3f} at {box.to_xyxy()}")
    
    # Save visualization if requested
    if output:
        visualize_detections(image, result, output_path=output)
        click.echo(f"\nVisualization saved to: {output}")
    
    # Save JSON if requested
    if json_output:
        with open(json_output, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        click.echo(f"JSON output saved to: {json_output}")


@cli.command()
@click.argument('image_dir', type=click.Path(exists=True, file_okay=False))
@click.argument('prompts', nargs=-1, required=True)
@click.option('--model', '-m', default='owlv2-base', help='Model to use')
@click.option('--device', '-d', default=None, help='Device (cuda/cpu)')
@click.option('--confidence', '-c', default=0.3, type=float, help='Confidence threshold')
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory for visualizations')
@click.option('--pattern', default='*.jpg', help='File pattern to match')
def detect_batch(image_dir, prompts, model, device, confidence, output_dir, pattern):
    """
    Detect objects in multiple images from a directory.
    
    Example:
        perceptra detect-batch images/ person car --pattern "*.jpg"
    """
    click.echo(f"Loading model: {model}")
    detector = ZeroShotDetector(
        model_name=model,
        device=device,
        confidence_threshold=confidence
    )
    
    # Find all images
    image_dir = Path(image_dir)
    image_paths = list(image_dir.glob(pattern))
    
    if not image_paths:
        click.echo(f"No images found matching pattern: {pattern}")
        return
    
    click.echo(f"Found {len(image_paths)} images")
    click.echo(f"Prompts: {', '.join(prompts)}")
    
    # Create output directory if needed
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each image
    total_detections = 0
    with click.progressbar(image_paths, label='Processing images') as bar:
        for img_path in bar:
            image = Image.open(img_path)
            result = detector.detect(image, list(prompts))
            total_detections += len(result)
            
            if output_dir:
                output_path = output_dir / f"{img_path.stem}_detected{img_path.suffix}"
                visualize_detections(image, result, output_path=str(output_path))
    
    click.echo(f"\nTotal detections: {total_detections} across {len(image_paths)} images")
    if output_dir:
        click.echo(f"Visualizations saved to: {output_dir}")


@cli.command()
def list_models():
    """List all available models."""
    models = ModelRegistry.list_models()
    click.echo("Available models:")
    for model in sorted(models):
        click.echo(f"  - {model}")


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind')
@click.option('--port', default=8000, type=int, help='Port to bind')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def serve(host, port, reload):
    """
    Start the REST API server.
    
    Example:
        perceptra serve --port 8000
    """
    try:
        import uvicorn
        from perceptra_zero_shot.api.main import app
        
        click.echo(f"Starting API server on http://{host}:{port}")
        click.echo("API docs available at /docs")
        
        uvicorn.run(
            "perceptra_zero_shot.api.main:app",
            host=host,
            port=port,
            reload=reload
        )
    except ImportError:
        click.echo("Error: FastAPI and uvicorn are required for API server.")
        click.echo("Install with: pip install perceptra-zero-shot[api]")
        raise click.Abort()


if __name__ == '__main__':
    cli()