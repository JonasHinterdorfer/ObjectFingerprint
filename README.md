# 3D Object Generation with W3C PROV Provenance Tracking

A Python project for generating 3D geometric objects with full W3C PROV-O provenance tracking. Generate colored 3D meshes (sphere, cube, cylinder), render them to 2D images, and create standards-compliant provenance records.

## Features

- **3D Object Generation**: Create spheres, cubes, and cylinders with customizable size, color, and resolution
- **Multi-format Export**: Save 3D models as PLY, OBJ, or STL
- **2D Rendering**: Render 3D objects to PNG images with configurable camera and lighting
- **W3C PROV-O Provenance**: Track full generation provenance with entities, activities, agents, and relationships
- **CLI Interface**: Easy-to-use command-line tool with configurable options

## Project Structure

```
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── src/
│   ├── __init__.py
│   ├── generator.py          # 3D object generation
│   ├── provenance.py         # PROV document creation and export
│   ├── renderer.py           # 3D to 2D image rendering
│   └── main.py               # CLI entry point
├── output/                   # Generated files
├── tests/
│   └── test_generator.py     # Unit tests
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

Generate a red sphere (default):
```bash
python -m src.main --shape sphere --color "255,0,0" --size 1.0
```

Generate a green cube as OBJ:
```bash
python -m src.main --shape cube --color "0,255,0" --size 2.0 --format obj
```

Generate a cylinder without rendering:
```bash
python -m src.main --shape cylinder --size 1.5 --no-render
```

Custom output directory and resolution:
```bash
python -m src.main --shape sphere --output-dir ./my_output --resolution 30
```

### CLI Arguments

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
| `--verbose` | `false` | Enable debug logging |

### Python API

```python
from src.generator import ObjectGenerator
from src.provenance import ProvenanceTracker
from src.renderer import MeshRenderer

# Generate a 3D sphere
generator = ObjectGenerator(shape="sphere", size=1.0, color=(255, 0, 0))
mesh = generator.generate()
model_path = generator.export("output/my_sphere", file_format="ply")

# Track provenance
tracker = ProvenanceTracker("MyProject")
tracker.record_agent("software", "3DProvenance", "1.0.0")
tracker.record_activity("gen", "Generate sphere", parameters=generator.get_parameters())
tracker.record_entity("model", "3DModel", model_path)
tracker.record_generation("model", "gen")
tracker.record_attribution("model", "software")
prov_path = tracker.export_json("output/provenance")

# Render to image
renderer = MeshRenderer(width=800, height=600)
image_path = renderer.render_to_image(mesh, "output/my_sphere")
```

## API Documentation

### `ObjectGenerator`

Class for generating 3D geometric objects.

- **`__init__(shape, size, color, resolution)`**: Initialize with shape type, size, RGB color, and resolution.
- **`generate()`**: Create the 3D mesh. Returns an Open3D `TriangleMesh`.
- **`export(filepath, file_format)`**: Save mesh to file. Returns the output path.
- **`get_parameters()`**: Get generation parameters as a dictionary.
- **`get_mesh()`**: Return the generated mesh (or None if not generated).

### `ProvenanceTracker`

W3C PROV-O compliant provenance document builder.

- **`record_activity(activity_id, description, parameters)`**: Record a generation activity.
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

- **Entity**: The generated 3D model and rendered 2D image
- **Activity**: The generation process with parameters (shape, size, color)
- **Agent**: The software that performed the generation
- **Relationships**:
  - `wasGeneratedBy`: Links model/image to the generation activity
  - `wasAttributedTo`: Links model/image to the software agent
  - `wasDerivedFrom`: Links rendered image to source 3D model

## Running Tests

```bash
python -m pytest tests/ -v
```

## License

See repository for license information.
