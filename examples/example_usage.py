"""Example usage of the 3D object scanning and generation project.

Demonstrates how to use the camera scanner, generator, renderer, and
provenance tracker programmatically (without the CLI).
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generator import ObjectGenerator
from src.provenance import ProvenanceTracker
from src.renderer import MeshRenderer
from src.scanner import CameraScanner


def scan_example() -> None:
    """Demonstrate camera-based 3D object scanning."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    print("=== Camera Scanning Example ===\n")

    # 1. Initialize scanner
    print("Initializing camera scanner...")
    scanner = CameraScanner(camera_index=0, frame_width=1280, frame_height=720)

    # 2. Capture a frame from the camera
    print("Capturing frame from camera...")
    try:
        frame = scanner.capture_frame()
        frame_path = scanner.save_frame(frame, str(output_dir / "example_scan"))
        print(f"  Saved scan frame to: {frame_path}")
    except RuntimeError as e:
        print(f"  Camera not available: {e}")
        print("  (This is expected in environments without a camera)")
        return

    # 3. Track provenance for the scan
    print("\nCreating provenance record for the scan...")
    tracker = ProvenanceTracker("ScanExample")
    tracker.record_agent("software", "3DProvenance", "1.0.0")
    tracker.record_activity(
        "camera_scan",
        "Scan 3D object with camera",
        parameters=scanner.get_parameters(),
    )
    tracker.record_entity("scan_frame_0", "ScannedImage", frame_path)
    tracker.record_generation("scan_frame_0", "camera_scan")
    tracker.record_attribution("scan_frame_0", "software")

    # 4. Export provenance
    prov_json = tracker.export_json(str(output_dir / "scan_provenance"))
    print(f"  Provenance JSON: {prov_json}")

    print("\nScan example complete!")


def generate_example() -> None:
    """Demonstrate programmatic 3D object generation."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    print("\n=== Generation Example ===\n")

    # 1. Generate a red sphere
    print("Generating a red sphere...")
    sphere_gen = ObjectGenerator(shape="sphere", size=1.0, color=(255, 0, 0))
    sphere_mesh = sphere_gen.generate()
    sphere_path = sphere_gen.export(str(output_dir / "example_sphere"), "ply")
    print(f"  Saved 3D model to: {sphere_path}")

    # 2. Generate a green cube
    print("Generating a green cube...")
    cube_gen = ObjectGenerator(shape="cube", size=1.5, color=(0, 255, 0))
    cube_mesh = cube_gen.generate()
    cube_path = cube_gen.export(str(output_dir / "example_cube"), "obj")
    print(f"  Saved 3D model to: {cube_path}")

    # 3. Generate a blue cylinder
    print("Generating a blue cylinder...")
    cyl_gen = ObjectGenerator(shape="cylinder", size=1.0, color=(0, 0, 255))
    cyl_mesh = cyl_gen.generate()
    cyl_path = cyl_gen.export(str(output_dir / "example_cylinder"), "stl")
    print(f"  Saved 3D model to: {cyl_path}")

    # 4. Track provenance for the sphere
    print("\nCreating provenance record for the sphere...")
    tracker = ProvenanceTracker("ExampleProject")
    tracker.record_agent("software", "3DProvenance", "1.0.0")
    tracker.record_activity(
        "sphere_generation",
        "Generate red sphere",
        parameters=sphere_gen.get_parameters(),
    )
    tracker.record_entity("sphere_model", "3DModel", sphere_path)
    tracker.record_generation("sphere_model", "sphere_generation")
    tracker.record_attribution("sphere_model", "software")

    # 5. Export provenance
    prov_json = tracker.export_json(str(output_dir / "example_provenance"))
    prov_xml = tracker.export_xml(str(output_dir / "example_provenance"))
    print(f"  Provenance JSON: {prov_json}")
    print(f"  Provenance XML: {prov_xml}")

    print("\nGeneration example complete!")


def main() -> None:
    """Run example usage demonstrating all core features."""
    scan_example()
    generate_example()
    print("\nDone! All files saved to the 'output' directory.")


if __name__ == "__main__":
    main()
