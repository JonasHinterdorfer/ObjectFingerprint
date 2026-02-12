"""CLI entry point for 3D object generation with provenance tracking.

Provides a command-line interface for generating 3D objects, rendering
them to 2D images, and creating W3C PROV provenance documents.

Usage:
    python -m src.main --shape sphere --color "255,0,0" --size 1.0
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

from src import __version__
from src.generator import ObjectGenerator, SUPPORTED_SHAPES, SUPPORTED_FORMATS
from src.provenance import ProvenanceTracker
from src.renderer import MeshRenderer


def parse_color(color_str: str) -> Tuple[int, int, int]:
    """Parse a comma-separated RGB color string.

    Args:
        color_str: Color string in format 'R,G,B' with values in [0, 255].

    Returns:
        Tuple of (R, G, B) integers.

    Raises:
        argparse.ArgumentTypeError: If the format is invalid.
    """
    try:
        parts = [int(c.strip()) for c in color_str.split(",")]
        if len(parts) != 3:
            raise ValueError("Expected 3 values")
        if not all(0 <= c <= 255 for c in parts):
            raise ValueError("Values must be in [0, 255]")
        return (parts[0], parts[1], parts[2])
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid color '{color_str}'. Use format 'R,G,B' (e.g., '255,0,0'): {exc}"
        )


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Generate 3D objects with W3C PROV provenance tracking.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m src.main --shape sphere --color '255,0,0' --size 1.0\n"
            "  python -m src.main --shape cube --color '0,255,0' --size 2.0 --format obj\n"
            "  python -m src.main --shape cylinder --output-dir ./my_output\n"
        ),
    )
    parser.add_argument(
        "--shape",
        type=str,
        choices=SUPPORTED_SHAPES,
        default="sphere",
        help="Shape of the 3D object to generate (default: sphere)",
    )
    parser.add_argument(
        "--color",
        type=parse_color,
        default=(255, 0, 0),
        help="RGB color as 'R,G,B' with values 0-255 (default: '255,0,0')",
    )
    parser.add_argument(
        "--size",
        type=float,
        default=1.0,
        help="Scale factor for the object (default: 1.0)",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=20,
        help="Tessellation resolution for curved surfaces (default: 20)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=SUPPORTED_FORMATS,
        default="ply",
        help="3D model export format (default: ply)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory for generated files (default: output)",
    )
    parser.add_argument(
        "--render-width",
        type=int,
        default=800,
        help="Rendered image width in pixels (default: 800)",
    )
    parser.add_argument(
        "--render-height",
        type=int,
        default=600,
        help="Rendered image height in pixels (default: 600)",
    )
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Skip rendering to 2D image",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = f"{args.shape}_{args.size}"

        # Generate 3D object
        generator = ObjectGenerator(
            shape=args.shape,
            size=args.size,
            color=args.color,
            resolution=args.resolution,
        )
        mesh = generator.generate()
        model_path = generator.export(
            str(output_dir / base_name), file_format=args.format
        )
        logger.info("3D model saved to: %s", model_path)

        # Initialize provenance tracking
        tracker = ProvenanceTracker()
        tracker.record_agent("software", "3DProvenance", __version__)
        tracker.record_activity(
            "generation",
            f"Generate {args.shape} 3D object",
            parameters=generator.get_parameters(),
        )
        tracker.record_entity(
            "model_3d", "3DModel", model_path,
            attributes={"format": args.format},
        )
        tracker.record_generation("model_3d", "generation")
        tracker.record_attribution("model_3d", "software")

        # Render to image
        if not args.no_render:
            renderer = MeshRenderer(
                width=args.render_width,
                height=args.render_height,
            )
            image_path = renderer.render_to_image(
                mesh, str(output_dir / base_name)
            )
            logger.info("Rendered image saved to: %s", image_path)

            tracker.record_entity(
                "rendered_image", "RenderedImage", image_path,
                attributes={
                    "width": str(args.render_width),
                    "height": str(args.render_height),
                },
            )
            tracker.record_generation("rendered_image", "generation")
            tracker.record_attribution("rendered_image", "software")
            tracker.record_derivation("rendered_image", "model_3d")

        # Export provenance
        prov_json_path = tracker.export_json(str(output_dir / f"{base_name}_provenance"))
        logger.info("Provenance JSON saved to: %s", prov_json_path)

        print(f"Successfully generated {args.shape}:")
        print(f"  3D Model: {model_path}")
        if not args.no_render:
            print(f"  Image:    {image_path}")
        print(f"  Provenance: {prov_json_path}")
        return 0

    except Exception as exc:
        logger.error("Error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
