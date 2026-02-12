# 3D Object Fingerprinting with Camera Scanning and W3C PROV Provenance Tracking

A Python project for 3D object fingerprinting through camera-based scanning and programmatic generation, with full W3C PROV-O provenance tracking. Scan real-world objects with a camera or generate colored 3D meshes (sphere, cube, cylinder), render them to 2D images, and create standards-compliant provenance records.

## Features

- **Camera Scanning**: Capture images of 3D objects using a webcam for object fingerprinting
- **3D Object Generation**: Create spheres, cubes, and cylinders with customizable size, color, and resolution
- **Multi-format Export**: Save 3D models as PLY, OBJ, or STL
- **2D Rendering**: Render 3D objects to PNG images with configurable camera and lighting
- **W3C PROV-O Provenance**: Track full generation/scanning provenance with entities, activities, agents, and relationships
- **CLI Interface**: Easy-to-use command-line tool with `generate` and `scan` subcommands

## Project Structure

```
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── src/
│   ├── __init__.py
│   ├── generator.py          # 3D object generation
│   ├── scanner.py            # Camera-based 3D object scanning
│   ├── provenance.py         # PROV document creation and export
│   ├── renderer.py           # 3D to 2D image rendering
│   └── main.py               # CLI entry point
├── output/                   # Generated files
├── tests/
│   ├── test_generator.py     # Unit tests for generator, provenance, CLI
│   └── test_scanner.py       # Unit tests for camera scanner
└── examples/
    └── example_usage.py      # Example scripts
```

## Installation

### Prerequisites

- Python 3.9 or higher

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd ObjectFingerprint

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command-Line Interface

#### Scan a 3D object with the camera

Capture a single frame:
```bash
python -m src.main scan
```

Capture multiple frames for 3D scanning:
```bash
python -m src.main scan --num-frames 10 --delay 1000
```

Use a specific camera with custom resolution:
```bash
python -m src.main scan --camera-index 1 --frame-width 1920 --frame-height 1080
```

#### Generate a 3D object programmatically

Generate a red sphere (default):
```bash
python -m src.main generate --shape sphere --color "255,0,0" --size 1.0
```

Generate a green cube as OBJ:
```bash
python -m src.main generate --shape cube --color "0,255,0" --size 2.0 --format obj
```

Generate a cylinder without rendering:
```bash
python -m src.main generate --shape cylinder --size 1.5 --no-render
```

### Scan CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--camera-index` | `0` | Camera device index |
| `--num-frames` | `1` | Number of frames to capture |
| `--frame-width` | `1280` | Capture width in pixels |
| `--frame-height` | `720` | Capture height in pixels |
| `--delay` | `500` | Delay between captures (ms) |
| `--output-dir` | `output` | Output directory |
| `--prefix` | `scan` | Filename prefix for frames |

### Generate CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--shape` | `sphere` | Shape: `sphere`, `cube`, or `cylinder` |
| `--color` | `255,0,0` | RGB color as `R,G,B` (0-255) |
| `--size` | `1.0` | Scale factor for the object |
| `--resolution` | `20` | Tessellation resolution |
| `--format` | `ply` | Export format: `ply`, `obj`, `stl` |
| `--output-dir` | `output` | Output directory |
| `--render-width` | `800` | Rendered image width (px) |
| `--render-height` | `600` | Rendered image height (px) |
| `--no-render` | `false` | Skip 2D image rendering |

### Python API

```python
from src.scanner import CameraScanner
from src.generator import ObjectGenerator
from src.provenance import ProvenanceTracker
from src.renderer import MeshRenderer

# Scan a 3D object with the camera
scanner = CameraScanner(camera_index=0, frame_width=1280, frame_height=720)
frame = scanner.capture_frame()
frame_path = scanner.save_frame(frame, "output/scan_001")

# Or capture multiple frames
frames = scanner.capture_multiple(num_frames=5, delay_ms=1000)
saved_paths = scanner.save_all_frames("output", prefix="object_scan")

# Track provenance for scanning
tracker = ProvenanceTracker("ScanProject")
tracker.record_agent("software", "3DProvenance", "1.0.0")
tracker.record_activity("scan", "Scan 3D object", parameters=scanner.get_parameters())
tracker.record_entity("scan_frame", "ScannedImage", frame_path)
tracker.record_generation("scan_frame", "scan")
tracker.record_attribution("scan_frame", "software")
prov_path = tracker.export_json("output/scan_provenance")

# Generate a 3D object programmatically
generator = ObjectGenerator(shape="sphere", size=1.0, color=(255, 0, 0))
mesh = generator.generate()
model_path = generator.export("output/my_sphere", file_format="ply")

# Render to image
renderer = MeshRenderer(width=800, height=600)
image_path = renderer.render_to_image(mesh, "output/my_sphere")
```

## API Documentation

### `CameraScanner`

Class for capturing images from a camera for 3D object scanning.

- **`__init__(camera_index, frame_width, frame_height)`**: Initialize with camera device index and resolution.
- **`capture_frame()`**: Capture a single frame. Returns a NumPy array (BGR).
- **`capture_multiple(num_frames, delay_ms)`**: Capture multiple frames with delay between each.
- **`save_frame(frame, filepath)`**: Save a frame to a PNG file. Returns the output path.
- **`save_all_frames(output_dir, prefix)`**: Save all captured frames. Returns list of paths.
- **`get_captured_frames()`**: Return all captured frames.
- **`get_frame_count()`**: Return the number of captured frames.
- **`clear_frames()`**: Clear all captured frames from memory.
- **`get_parameters()`**: Get scanner parameters as a dictionary.

### `ObjectGenerator`

Class for generating 3D geometric objects.

- **`__init__(shape, size, color, resolution)`**: Initialize with shape type, size, RGB color, and resolution.
- **`generate()`**: Create the 3D mesh. Returns an Open3D `TriangleMesh`.
- **`export(filepath, file_format)`**: Save mesh to file. Returns the output path.
- **`get_parameters()`**: Get generation parameters as a dictionary.
- **`get_mesh()`**: Return the generated mesh (or None if not generated).

### `ProvenanceTracker`

W3C PROV-O compliant provenance document builder.

- **`record_activity(activity_id, description, parameters)`**: Record a generation/scanning activity.
- **`record_entity(entity_id, entity_type, filepath, attributes)`**: Record an output entity.
- **`record_agent(agent_id, software_name, version)`**: Record a software agent.
- **`record_generation(entity_id, activity_id)`**: Link entity to generating activity (`wasGeneratedBy`).
- **`record_attribution(entity_id, agent_id)`**: Link entity to agent (`wasAttributedTo`).
- **`record_derivation(derived_id, source_id)`**: Link derived entity to source (`wasDerivedFrom`).
- **`export_json(filepath)`**: Export as PROV-JSON.
- **`export_xml(filepath)`**: Export as PROV-XML.

### `MeshRenderer`

Renders Open3D meshes to 2D PNG images.

- **`__init__(width, height, camera_position, look_at, up_vector)`**: Configure rendering.
- **`render_to_image(mesh, filepath, background_color)`**: Render and save image.
- **`get_parameters()`**: Get rendering parameters as a dictionary.

## PROV Model

The provenance model follows the [W3C PROV-O](https://www.w3.org/TR/prov-o/) standard:

- **Entity**: Scanned images, generated 3D models, and rendered 2D images
- **Activity**: The scanning or generation process with parameters
- **Agent**: The software that performed the scanning/generation
- **Relationships**:
  - `wasGeneratedBy`: Links scanned image/model/image to the activity
  - `wasAttributedTo`: Links entities to the software agent
  - `wasDerivedFrom`: Links rendered image to source 3D model

## Running Tests

```bash
python -m pytest tests/ -v
```

## License

See repository for license information.
