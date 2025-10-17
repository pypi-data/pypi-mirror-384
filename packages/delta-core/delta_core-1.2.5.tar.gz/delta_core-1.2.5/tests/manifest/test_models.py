import importlib.resources
import json
import unittest

from delta.manifest.models import Manifest, License, Input, Resource


class TestManifestPydanticModel(unittest.TestCase):
    def test_manifest_minimal(self):
        traversable = (
            importlib.resources.files("delta.manifest.v1_4")
            .joinpath("minimum.json")
        )
        with importlib.resources.as_file(traversable) as path:
            with open(path) as f:
                manifest_data = json.load(f)
        manifest = Manifest.model_validate(manifest_data)
        self.assertEqual(manifest.name, "Delta Twin name")
        self.assertEqual(manifest.description, "Delta Twin Description")
        self.assertIsNone(manifest.short_description)
        self.assertEqual(manifest.license, License())
        self.assertEqual(manifest.owner, "GAEL Systems")
        self.assertEqual(manifest.inputs, {})
        self.assertEqual(manifest.outputs, {})
        self.assertEqual(manifest.models, {})
        self.assertEqual(manifest.dependencies, {})

    def test_invalid_identifier(self):
        manifest_base_data = {
            "name": "valid",
            "description": "",
            "owner": "test",
        }
        with self.assertRaises(ValueError):
            manifest_data = manifest_base_data | {
                "resources": {"invalid-name": {"type": "integer", "value": 1}}
            }
            Manifest.model_validate(manifest_data)
        with self.assertRaises(ValueError):
            manifest_data = manifest_base_data | {
                "inputs": {"invalid-name": {"type": "integer", "value": 1}}
            }
            Manifest.model_validate(manifest_data)
        with self.assertRaises(ValueError):
            manifest_data = manifest_base_data | {
                "outputs": {"invalid-name": {"type": "integer", "value": 1}}
            }
            Manifest.model_validate(manifest_data)
