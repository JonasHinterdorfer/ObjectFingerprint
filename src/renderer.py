"""3D to 2D image rendering module.

Renders Open3D 3D meshes to 2D images with configurable camera position,
lighting, and resolution. Supports saving as PNG.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import open3d as o3d

logger = logging.getLogger(__name__)


class MeshRenderer:
    """Renders Open3D meshes to 2D images using offscreen rendering.

    Attributes:
        width: Image width in pixels.
        height: Image height in pixels.
        camera_position: Camera position as (x, y, z).
        look_at: Point the camera looks at as (x, y, z).
        up_vector: Camera up direction as (x, y, z).
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        camera_position: Tuple[float, float, float] = (2.0, 2.0, 2.0),
        look_at: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        up_vector: Tuple[float, float, float] = (0.0, 1.0, 0.0),
    ) -> None:
        """Initialize the renderer.

        Args:
            width: Image width in pixels.
            height: Image height in pixels.
            camera_position: Camera position as (x, y, z).
            look_at: Point the camera looks at as (x, y, z).
            up_vector: Camera up direction as (x, y, z).

        Raises:
            ValueError: If width or height is non-positive.
        """
        if width <= 0 or height <= 0:
            raise ValueError(
                f"Width and height must be positive, got ({width}, {height})."
            )
        self.width = width
        self.height = height
        self.camera_position = camera_position
        self.look_at = look_at
        self.up_vector = up_vector
        logger.info(
            "MeshRenderer initialized: %dx%d, camera=%s",
            width, height, camera_position,
        )

    def render_to_image(
        self,
        mesh: o3d.geometry.TriangleMesh,
        filepath: str,
        background_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> str:
        """Render a mesh to a PNG image file.

        Uses Open3D's offscreen rendering to produce a 2D image of the mesh.

        Args:
            mesh: The Open3D triangle mesh to render.
            filepath: Output file path (without extension).
            background_color: Background color as normalized RGB (0.0-1.0).

        Returns:
            The full path of the saved PNG file.
        """
        output_path = Path(filepath).with_suffix(".png")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        renderer = o3d.visualization.rendering.OffscreenRenderer(
            self.width, self.height
        )
        renderer.scene.set_background(
            np.array([*background_color, 1.0])
        )

        material = o3d.visualization.rendering.MaterialRecord()
        material.shader = "defaultLit"
        renderer.scene.add_geometry("mesh", mesh, material)

        renderer.scene.scene.set_sun_light(
            [0.577, -0.577, -0.577], [1.0, 1.0, 1.0], 100000
        )
        renderer.scene.scene.enable_sun_light(True)

        renderer.setup_camera(
            60.0,
            [*self.look_at],
            [*self.camera_position],
            [*self.up_vector],
        )

        img = renderer.render_to_image()
        o3d.io.write_image(str(output_path), img)
        logger.info("Rendered image saved to %s", output_path)
        return str(output_path)

    def get_parameters(self) -> dict:
        """Return the rendering parameters as a dictionary.

        Returns:
            Dictionary with width, height, camera_position, look_at, up_vector.
        """
        return {
            "width": self.width,
            "height": self.height,
            "camera_position": list(self.camera_position),
            "look_at": list(self.look_at),
            "up_vector": list(self.up_vector),
        }
