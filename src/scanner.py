"""Camera-based 3D object scanning module.

Captures images from a camera (webcam) for 3D object scanning. Supports
capturing single frames or multiple frames from different angles, saving
them as PNG images that can be used for 3D reconstruction.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_CAMERA_INDEX = 0
DEFAULT_FRAME_WIDTH = 1280
DEFAULT_FRAME_HEIGHT = 720


class CameraScanner:
    """Captures images from a camera for 3D object scanning.

    Attributes:
        camera_index: Index of the camera device to use.
        frame_width: Capture width in pixels.
        frame_height: Capture height in pixels.
    """

    def __init__(
        self,
        camera_index: int = DEFAULT_CAMERA_INDEX,
        frame_width: int = DEFAULT_FRAME_WIDTH,
        frame_height: int = DEFAULT_FRAME_HEIGHT,
    ) -> None:
        """Initialize the camera scanner.

        Args:
            camera_index: Index of the camera device (0 for default webcam).
            frame_width: Desired capture width in pixels.
            frame_height: Desired capture height in pixels.

        Raises:
            ValueError: If camera_index is negative, or dimensions are
                non-positive.
        """
        if camera_index < 0:
            raise ValueError(
                f"Camera index must be non-negative, got {camera_index}."
            )
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError(
                f"Frame dimensions must be positive, got ({frame_width}, {frame_height})."
            )

        self.camera_index = camera_index
        self.frame_width = frame_width
        self.frame_height = frame_height
        self._captured_frames: List[np.ndarray] = []
        logger.info(
            "CameraScanner initialized: camera=%d, resolution=%dx%d",
            camera_index, frame_width, frame_height,
        )

    def capture_frame(self) -> np.ndarray:
        """Capture a single frame from the camera.

        Returns:
            The captured frame as a NumPy array (BGR format).

        Raises:
            RuntimeError: If the camera cannot be opened or frame capture
                fails.
        """
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera at index {self.camera_index}."
            )

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                raise RuntimeError("Failed to capture frame from camera.")
            self._captured_frames.append(frame)
            logger.info(
                "Captured frame %d: %dx%d",
                len(self._captured_frames), frame.shape[1], frame.shape[0],
            )
            return frame
        finally:
            cap.release()

    def capture_multiple(self, num_frames: int, delay_ms: int = 500) -> List[np.ndarray]:
        """Capture multiple frames from the camera.

        Opens the camera once and captures the specified number of frames
        with a delay between each capture to allow repositioning.

        Args:
            num_frames: Number of frames to capture.
            delay_ms: Delay between captures in milliseconds.

        Returns:
            List of captured frames as NumPy arrays.

        Raises:
            ValueError: If num_frames is not positive.
            RuntimeError: If the camera cannot be opened.
        """
        if num_frames <= 0:
            raise ValueError(
                f"Number of frames must be positive, got {num_frames}."
            )

        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera at index {self.camera_index}."
            )

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

        frames: List[np.ndarray] = []
        try:
            for i in range(num_frames):
                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning("Failed to capture frame %d", i + 1)
                    continue
                frames.append(frame)
                self._captured_frames.append(frame)
                logger.info(
                    "Captured frame %d/%d: %dx%d",
                    i + 1, num_frames, frame.shape[1], frame.shape[0],
                )
                if i < num_frames - 1:
                    cv2.waitKey(delay_ms)
        finally:
            cap.release()

        logger.info("Captured %d of %d requested frames", len(frames), num_frames)
        return frames

    def save_frame(
        self,
        frame: np.ndarray,
        filepath: str,
    ) -> str:
        """Save a captured frame to a PNG file.

        Args:
            frame: The frame to save (NumPy array in BGR format).
            filepath: Output file path (without extension).

        Returns:
            The full path of the saved PNG file.

        Raises:
            ValueError: If the frame is empty or invalid.
        """
        if frame is None or frame.size == 0:
            raise ValueError("Cannot save an empty frame.")

        output_path = Path(filepath).with_suffix(".png")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), frame)
        logger.info("Saved frame to %s", output_path)
        return str(output_path)

    def save_all_frames(self, output_dir: str, prefix: str = "scan") -> List[str]:
        """Save all captured frames to PNG files.

        Args:
            output_dir: Directory to save frames in.
            prefix: Filename prefix for saved frames.

        Returns:
            List of file paths of saved frames.

        Raises:
            RuntimeError: If no frames have been captured.
        """
        if not self._captured_frames:
            raise RuntimeError("No frames captured. Call capture_frame() first.")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_paths: List[str] = []
        for i, frame in enumerate(self._captured_frames):
            frame_path = str(output_path / f"{prefix}_{i:04d}")
            path = self.save_frame(frame, frame_path)
            saved_paths.append(path)

        logger.info("Saved %d frames to %s", len(saved_paths), output_dir)
        return saved_paths

    def get_captured_frames(self) -> List[np.ndarray]:
        """Return all captured frames.

        Returns:
            List of captured frames as NumPy arrays.
        """
        return list(self._captured_frames)

    def get_frame_count(self) -> int:
        """Return the number of captured frames.

        Returns:
            Number of frames captured so far.
        """
        return len(self._captured_frames)

    def clear_frames(self) -> None:
        """Clear all captured frames from memory."""
        self._captured_frames.clear()
        logger.info("Cleared all captured frames")

    def get_parameters(self) -> dict:
        """Return the scanner parameters as a dictionary.

        Returns:
            Dictionary with camera_index, frame_width, frame_height,
            and frames_captured.
        """
        return {
            "camera_index": self.camera_index,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "frames_captured": len(self._captured_frames),
        }
