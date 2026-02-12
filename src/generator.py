"""3D object generation module.

Provides class-based generation of 3D geometric objects (sphere, cube, cylinder)
using Open3D, with support for customizable parameters, vertex colors, and
export to PLY, OBJ, and STL formats.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import open3d as o3d

logger = logging.getLogger(__name__)

SUPPORTED_SHAPES = ("sphere", "cube", "cylinder")
SUPPORTED_FORMATS = ("ply", "obj", "stl")


class ObjectGenerator:
    """Generates 3D geometric objects with configurable parameters.

    Attributes:
        shape: The type of 3D shape to generate.
        size: Scale factor for the object.
        color: RGB color tuple with values in [0, 255].
        resolution: Tessellation resolution for curved surfaces.
    """

    def __init__(
        self,
        shape: str = "sphere",
        size: float = 1.0,
        color: Tuple[int, int, int] = (255, 0, 0),
        resolution: int = 20,
    ) -> None:
        """Initialize the object generator.

        Args:
            shape: Shape type - one of 'sphere', 'cube', 'cylinder'.
            size: Scale factor for the generated object.
            color: RGB color tuple with values in [0, 255].
            resolution: Tessellation resolution for curved surfaces.

        Raises:
            ValueError: If shape is not supported, size is non-positive,
                color values are out of range, or resolution is non-positive.
        """
        if shape not in SUPPORTED_SHAPES:
            raise ValueError(
                f"Unsupported shape '{shape}'. Must be one of {SUPPORTED_SHAPES}."
            )
        if size <= 0:
            raise ValueError(f"Size must be positive, got {size}.")
        if not all(0 <= c <= 255 for c in color):
            raise ValueError(
                f"Color values must be in [0, 255], got {color}."
            )
        if resolution <= 0:
            raise ValueError(
                f"Resolution must be positive, got {resolution}."
            )

        self.shape = shape
        self.size = size
        self.color = color
        self.resolution = resolution
        self._mesh: Optional[o3d.geometry.TriangleMesh] = None
        logger.info(
            "ObjectGenerator initialized: shape=%s, size=%s, color=%s",
            shape, size, color,
        )

    def generate(self) -> o3d.geometry.TriangleMesh:
        """Generate the 3D mesh based on the configured parameters.

        Returns:
            The generated Open3D triangle mesh.
        """
        logger.info("Generating %s with size=%s", self.shape, self.size)

        if self.shape == "sphere":
            self._mesh = o3d.geometry.TriangleMesh.create_sphere(
                radius=self.size, resolution=self.resolution
            )
        elif self.shape == "cube":
            self._mesh = o3d.geometry.TriangleMesh.create_box(
                width=self.size, height=self.size, depth=self.size
            )
            # Center the cube at origin
            self._mesh.translate(-np.array([self.size, self.size, self.size]) / 2.0)
        elif self.shape == "cylinder":
            self._mesh = o3d.geometry.TriangleMesh.create_cylinder(
                radius=self.size / 2.0,
                height=self.size,
                resolution=self.resolution,
            )

        self._mesh.compute_vertex_normals()
        self._apply_color()
        logger.info("Generated %s with %d vertices", self.shape, len(self._mesh.vertices))
        return self._mesh

    def _apply_color(self) -> None:
        """Apply uniform RGB color to all vertices."""
        if self._mesh is None:
            return
        color_normalized = np.array(self.color) / 255.0
        self._mesh.paint_uniform_color(color_normalized)
        logger.debug("Applied color %s to mesh", self.color)

    def get_mesh(self) -> Optional[o3d.geometry.TriangleMesh]:
        """Return the generated mesh, or None if not yet generated.

        Returns:
            The generated mesh, or None.
        """
        return self._mesh

    def export(
        self,
        filepath: str,
        file_format: str = "ply",
    ) -> str:
        """Export the generated mesh to a file.

        Args:
            filepath: Output file path (without extension).
            file_format: Export format - one of 'ply', 'obj', 'stl'.

        Returns:
            The full path of the exported file.

        Raises:
            ValueError: If format is unsupported.
            RuntimeError: If no mesh has been generated yet.
        """
        if file_format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format '{file_format}'. Must be one of {SUPPORTED_FORMATS}."
            )
        if self._mesh is None:
            raise RuntimeError(
                "No mesh generated. Call generate() first."
            )

        output_path = Path(filepath).with_suffix(f".{file_format}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        o3d.io.write_triangle_mesh(str(output_path), self._mesh)
        logger.info("Exported mesh to %s", output_path)
        return str(output_path)

    def get_parameters(self) -> dict:
        """Return the generation parameters as a dictionary.

        Returns:
            Dictionary with shape, size, color, and resolution.
        """
        return {
            "shape": self.shape,
            "size": self.size,
            "color": list(self.color),
            "resolution": self.resolution,
        }
