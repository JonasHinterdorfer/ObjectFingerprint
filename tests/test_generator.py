"""Unit tests for the 3D object generator and provenance tracker."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

from src.generator import ObjectGenerator, SUPPORTED_SHAPES, SUPPORTED_FORMATS
from src.provenance import ProvenanceTracker
from src.main import parse_color, build_parser


class TestObjectGeneratorInit(unittest.TestCase):
    """Tests for ObjectGenerator initialization and validation."""

    def test_default_parameters(self) -> None:
        gen = ObjectGenerator()
        self.assertEqual(gen.shape, "sphere")
        self.assertEqual(gen.size, 1.0)
        self.assertEqual(gen.color, (255, 0, 0))
        self.assertEqual(gen.resolution, 20)

    def test_custom_parameters(self) -> None:
        gen = ObjectGenerator(
            shape="cube", size=2.5, color=(0, 128, 255), resolution=30
        )
        self.assertEqual(gen.shape, "cube")
        self.assertEqual(gen.size, 2.5)
        self.assertEqual(gen.color, (0, 128, 255))

    def test_invalid_shape(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            ObjectGenerator(shape="pyramid")
        self.assertIn("Unsupported shape", str(ctx.exception))

    def test_invalid_size_zero(self) -> None:
        with self.assertRaises(ValueError):
            ObjectGenerator(size=0)

    def test_invalid_size_negative(self) -> None:
        with self.assertRaises(ValueError):
            ObjectGenerator(size=-1.0)

    def test_invalid_color_out_of_range(self) -> None:
        with self.assertRaises(ValueError):
            ObjectGenerator(color=(256, 0, 0))

    def test_invalid_color_negative(self) -> None:
        with self.assertRaises(ValueError):
            ObjectGenerator(color=(-1, 0, 0))

    def test_invalid_resolution(self) -> None:
        with self.assertRaises(ValueError):
            ObjectGenerator(resolution=0)

    def test_get_parameters(self) -> None:
        gen = ObjectGenerator(shape="cylinder", size=3.0, color=(10, 20, 30))
        params = gen.get_parameters()
        self.assertEqual(params["shape"], "cylinder")
        self.assertEqual(params["size"], 3.0)
        self.assertEqual(params["color"], [10, 20, 30])


class TestObjectGeneratorGenerate(unittest.TestCase):
    """Tests for ObjectGenerator mesh generation."""

    def test_generate_sphere(self) -> None:
        gen = ObjectGenerator(shape="sphere", size=1.0, resolution=10)
        mesh = gen.generate()
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 0)
        self.assertGreater(len(mesh.triangles), 0)

    def test_generate_cube(self) -> None:
        gen = ObjectGenerator(shape="cube", size=1.0)
        mesh = gen.generate()
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 0)

    def test_generate_cylinder(self) -> None:
        gen = ObjectGenerator(shape="cylinder", size=1.0, resolution=10)
        mesh = gen.generate()
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 0)

    def test_mesh_has_colors(self) -> None:
        gen = ObjectGenerator(color=(255, 0, 0))
        mesh = gen.generate()
        self.assertTrue(mesh.has_vertex_colors())
        colors = np.asarray(mesh.vertex_colors)
        self.assertEqual(colors.shape[1], 3)
        np.testing.assert_array_almost_equal(colors[0], [1.0, 0.0, 0.0])

    def test_get_mesh_before_generate(self) -> None:
        gen = ObjectGenerator()
        self.assertIsNone(gen.get_mesh())

    def test_get_mesh_after_generate(self) -> None:
        gen = ObjectGenerator()
        gen.generate()
        self.assertIsNotNone(gen.get_mesh())

    def test_all_supported_shapes(self) -> None:
        for shape in SUPPORTED_SHAPES:
            gen = ObjectGenerator(shape=shape, resolution=5)
            mesh = gen.generate()
            self.assertGreater(
                len(mesh.vertices), 0, f"Shape '{shape}' produced no vertices"
            )


class TestObjectGeneratorExport(unittest.TestCase):
    """Tests for ObjectGenerator export functionality."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.gen = ObjectGenerator(shape="sphere", resolution=5)
        self.gen.generate()

    def test_export_ply(self) -> None:
        path = self.gen.export(os.path.join(self.tmpdir, "test"), "ply")
        self.assertTrue(path.endswith(".ply"))
        self.assertTrue(os.path.exists(path))

    def test_export_obj(self) -> None:
        path = self.gen.export(os.path.join(self.tmpdir, "test"), "obj")
        self.assertTrue(path.endswith(".obj"))
        self.assertTrue(os.path.exists(path))

    def test_export_stl(self) -> None:
        path = self.gen.export(os.path.join(self.tmpdir, "test"), "stl")
        self.assertTrue(path.endswith(".stl"))
        self.assertTrue(os.path.exists(path))

    def test_export_invalid_format(self) -> None:
        with self.assertRaises(ValueError):
            self.gen.export(os.path.join(self.tmpdir, "test"), "fbx")

    def test_export_no_mesh(self) -> None:
        gen = ObjectGenerator()
        with self.assertRaises(RuntimeError):
            gen.export(os.path.join(self.tmpdir, "test"))


class TestProvenanceTracker(unittest.TestCase):
    """Tests for ProvenanceTracker."""

    def setUp(self) -> None:
        self.tracker = ProvenanceTracker("TestProject")
        self.tmpdir = tempfile.mkdtemp()

    def test_record_activity(self) -> None:
        self.tracker.record_activity(
            "gen1", "Generate sphere", {"shape": "sphere"}
        )
        doc = self.tracker.get_document()
        records = list(doc.get_records())
        self.assertGreater(len(records), 0)

    def test_record_entity(self) -> None:
        self.tracker.record_entity("model", "3DModel", "/tmp/test.ply")
        doc = self.tracker.get_document()
        records = list(doc.get_records())
        self.assertGreater(len(records), 0)

    def test_record_agent(self) -> None:
        self.tracker.record_agent("sw", "TestSoftware", "1.0.0")
        doc = self.tracker.get_document()
        records = list(doc.get_records())
        self.assertGreater(len(records), 0)

    def test_record_generation(self) -> None:
        self.tracker.record_activity("gen1", "Generate")
        self.tracker.record_entity("model", "3DModel", "/tmp/test.ply")
        self.tracker.record_generation("model", "gen1")
        doc = self.tracker.get_document()
        records = list(doc.get_records())
        self.assertGreater(len(records), 2)

    def test_record_attribution(self) -> None:
        self.tracker.record_entity("model", "3DModel", "/tmp/test.ply")
        self.tracker.record_agent("sw", "TestSoftware", "1.0.0")
        self.tracker.record_attribution("model", "sw")
        doc = self.tracker.get_document()
        records = list(doc.get_records())
        self.assertGreater(len(records), 2)

    def test_record_derivation(self) -> None:
        self.tracker.record_entity("model", "3DModel", "/tmp/test.ply")
        self.tracker.record_entity("image", "RenderedImage", "/tmp/test.png")
        self.tracker.record_derivation("image", "model")
        doc = self.tracker.get_document()
        records = list(doc.get_records())
        self.assertGreater(len(records), 2)

    def test_export_json(self) -> None:
        self.tracker.record_activity("gen1", "Generate sphere")
        self.tracker.record_entity("model", "3DModel", "/tmp/test.ply")
        self.tracker.record_generation("model", "gen1")

        path = self.tracker.export_json(os.path.join(self.tmpdir, "prov"))
        self.assertTrue(path.endswith(".json"))
        self.assertTrue(os.path.exists(path))

        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

    def test_export_xml(self) -> None:
        self.tracker.record_activity("gen1", "Generate sphere")
        self.tracker.record_entity("model", "3DModel", "/tmp/test.ply")

        path = self.tracker.export_xml(os.path.join(self.tmpdir, "prov"))
        self.assertTrue(path.endswith(".xml"))
        self.assertTrue(os.path.exists(path))


class TestParseColor(unittest.TestCase):
    """Tests for CLI color parsing."""

    def test_valid_color(self) -> None:
        self.assertEqual(parse_color("255,0,0"), (255, 0, 0))

    def test_valid_color_with_spaces(self) -> None:
        self.assertEqual(parse_color("0, 128, 255"), (0, 128, 255))

    def test_invalid_color_not_enough_values(self) -> None:
        with self.assertRaises(Exception):
            parse_color("255,0")

    def test_invalid_color_out_of_range(self) -> None:
        with self.assertRaises(Exception):
            parse_color("256,0,0")

    def test_invalid_color_text(self) -> None:
        with self.assertRaises(Exception):
            parse_color("red")


class TestBuildParser(unittest.TestCase):
    """Tests for CLI argument parser."""

    def test_default_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.shape, "sphere")
        self.assertEqual(args.size, 1.0)
        self.assertEqual(args.format, "ply")

    def test_custom_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--shape", "cube",
            "--size", "2.5",
            "--format", "obj",
            "--output-dir", "/tmp/out",
            "--no-render",
        ])
        self.assertEqual(args.shape, "cube")
        self.assertEqual(args.size, 2.5)
        self.assertEqual(args.format, "obj")
        self.assertEqual(args.output_dir, "/tmp/out")
        self.assertTrue(args.no_render)


if __name__ == "__main__":
    unittest.main()
