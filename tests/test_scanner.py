"""Unit tests for the camera scanner module."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, PropertyMock

import numpy as np

from src.scanner import CameraScanner


class TestCameraScannerInit(unittest.TestCase):
    """Tests for CameraScanner initialization and validation."""

    def test_default_parameters(self) -> None:
        scanner = CameraScanner()
        self.assertEqual(scanner.camera_index, 0)
        self.assertEqual(scanner.frame_width, 1280)
        self.assertEqual(scanner.frame_height, 720)

    def test_custom_parameters(self) -> None:
        scanner = CameraScanner(camera_index=1, frame_width=640, frame_height=480)
        self.assertEqual(scanner.camera_index, 1)
        self.assertEqual(scanner.frame_width, 640)
        self.assertEqual(scanner.frame_height, 480)

    def test_invalid_camera_index(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            CameraScanner(camera_index=-1)
        self.assertIn("non-negative", str(ctx.exception))

    def test_invalid_frame_width(self) -> None:
        with self.assertRaises(ValueError):
            CameraScanner(frame_width=0)

    def test_invalid_frame_height(self) -> None:
        with self.assertRaises(ValueError):
            CameraScanner(frame_height=-1)

    def test_get_parameters(self) -> None:
        scanner = CameraScanner(camera_index=2, frame_width=800, frame_height=600)
        params = scanner.get_parameters()
        self.assertEqual(params["camera_index"], 2)
        self.assertEqual(params["frame_width"], 800)
        self.assertEqual(params["frame_height"], 600)
        self.assertEqual(params["frames_captured"], 0)


class TestCameraScannerCapture(unittest.TestCase):
    """Tests for CameraScanner frame capture with mocked camera."""

    def _make_fake_frame(self, width: int = 640, height: int = 480) -> np.ndarray:
        """Create a fake BGR frame for testing."""
        return np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)

    @patch("src.scanner.cv2.VideoCapture")
    def test_capture_frame_success(self, mock_cap_class: MagicMock) -> None:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        fake_frame = self._make_fake_frame()
        mock_cap.read.return_value = (True, fake_frame)
        mock_cap_class.return_value = mock_cap

        scanner = CameraScanner()
        frame = scanner.capture_frame()

        self.assertIsNotNone(frame)
        np.testing.assert_array_equal(frame, fake_frame)
        self.assertEqual(scanner.get_frame_count(), 1)
        mock_cap.release.assert_called_once()

    @patch("src.scanner.cv2.VideoCapture")
    def test_capture_frame_camera_not_opened(self, mock_cap_class: MagicMock) -> None:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cap_class.return_value = mock_cap

        scanner = CameraScanner()
        with self.assertRaises(RuntimeError) as ctx:
            scanner.capture_frame()
        self.assertIn("Cannot open camera", str(ctx.exception))

    @patch("src.scanner.cv2.VideoCapture")
    def test_capture_frame_read_fails(self, mock_cap_class: MagicMock) -> None:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)
        mock_cap_class.return_value = mock_cap

        scanner = CameraScanner()
        with self.assertRaises(RuntimeError) as ctx:
            scanner.capture_frame()
        self.assertIn("Failed to capture", str(ctx.exception))

    @patch("src.scanner.cv2.VideoCapture")
    @patch("src.scanner.cv2.waitKey")
    def test_capture_multiple_success(
        self, mock_waitkey: MagicMock, mock_cap_class: MagicMock
    ) -> None:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        frames = [self._make_fake_frame() for _ in range(3)]
        mock_cap.read.side_effect = [(True, f) for f in frames]
        mock_cap_class.return_value = mock_cap

        scanner = CameraScanner()
        result = scanner.capture_multiple(num_frames=3, delay_ms=100)

        self.assertEqual(len(result), 3)
        self.assertEqual(scanner.get_frame_count(), 3)
        mock_cap.release.assert_called_once()

    @patch("src.scanner.cv2.VideoCapture")
    def test_capture_multiple_invalid_count(self, mock_cap_class: MagicMock) -> None:
        scanner = CameraScanner()
        with self.assertRaises(ValueError):
            scanner.capture_multiple(num_frames=0)


class TestCameraScannerSave(unittest.TestCase):
    """Tests for CameraScanner frame saving."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()

    @patch("src.scanner.cv2.imwrite")
    def test_save_frame(self, mock_imwrite: MagicMock) -> None:
        mock_imwrite.return_value = True
        scanner = CameraScanner()
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

        path = scanner.save_frame(frame, os.path.join(self.tmpdir, "test"))
        self.assertTrue(path.endswith(".png"))
        mock_imwrite.assert_called_once()

    def test_save_frame_empty(self) -> None:
        scanner = CameraScanner()
        with self.assertRaises(ValueError):
            scanner.save_frame(np.array([]), os.path.join(self.tmpdir, "test"))

    def test_save_all_frames_no_captures(self) -> None:
        scanner = CameraScanner()
        with self.assertRaises(RuntimeError):
            scanner.save_all_frames(self.tmpdir)

    @patch("src.scanner.cv2.imwrite")
    @patch("src.scanner.cv2.VideoCapture")
    def test_save_all_frames(
        self, mock_cap_class: MagicMock, mock_imwrite: MagicMock
    ) -> None:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        fake_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, fake_frame)
        mock_cap_class.return_value = mock_cap
        mock_imwrite.return_value = True

        scanner = CameraScanner()
        scanner.capture_frame()
        paths = scanner.save_all_frames(self.tmpdir, prefix="test")

        self.assertEqual(len(paths), 1)
        self.assertTrue(paths[0].endswith(".png"))
        self.assertIn("test_0000", paths[0])


class TestCameraScannerFrameManagement(unittest.TestCase):
    """Tests for CameraScanner frame management."""

    @patch("src.scanner.cv2.VideoCapture")
    def test_get_captured_frames(self, mock_cap_class: MagicMock) -> None:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        fake_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, fake_frame)
        mock_cap_class.return_value = mock_cap

        scanner = CameraScanner()
        scanner.capture_frame()

        frames = scanner.get_captured_frames()
        self.assertEqual(len(frames), 1)
        np.testing.assert_array_equal(frames[0], fake_frame)

    @patch("src.scanner.cv2.VideoCapture")
    def test_clear_frames(self, mock_cap_class: MagicMock) -> None:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        fake_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, fake_frame)
        mock_cap_class.return_value = mock_cap

        scanner = CameraScanner()
        scanner.capture_frame()
        self.assertEqual(scanner.get_frame_count(), 1)

        scanner.clear_frames()
        self.assertEqual(scanner.get_frame_count(), 0)
        self.assertEqual(len(scanner.get_captured_frames()), 0)

    def test_initial_frame_count(self) -> None:
        scanner = CameraScanner()
        self.assertEqual(scanner.get_frame_count(), 0)

    def test_get_parameters_after_capture(self) -> None:
        scanner = CameraScanner()
        params = scanner.get_parameters()
        self.assertEqual(params["frames_captured"], 0)


if __name__ == "__main__":
    unittest.main()
