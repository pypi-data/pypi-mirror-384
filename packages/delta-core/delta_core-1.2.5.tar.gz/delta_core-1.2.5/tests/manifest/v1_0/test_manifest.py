import os
import json
import jsonschema
from unittest import TestCase
import tempfile

import delta.manifest.manifest as manifest
from delta.manifest.manifest import manifest_version, manifest_schema_filename


def _json_sample_path(version='1.0'):
    return os.path.join(os.path.dirname(__file__))


class TestManifest(TestCase):
    schema = None

    @classmethod
    def setUpClass(cls) -> None:
        # Load manifest schema: consider json is correct
        path = os.path.join(manifest._schema_path("1.0"),
                            manifest_schema_filename)
        fp = open(path)
        cls.schema = json.load(fp)
        print(f"Loaded Schema from {path}: {cls.schema}.")
        fp.close()

    def test_read_manifest(self):
        manifest_dict = manifest.read_manifest(os.path.join(
            _json_sample_path(), 'test_manifest_full.json'))
        self.assertEqual(manifest_dict['name'], 'Delta Twin name')

    def test_write_manifest_minimal(self):
        file_path = manifest.write_manifest()
        self.assertTrue(os.path.exists(file_path))
        data = manifest.read_manifest(file_path)
        os.remove(file_path)
        self.assertTrue(manifest.check_manifest(data))

    def test_write_manifest_to_dest(self):
        my_file_destination = tempfile.NamedTemporaryFile().name
        file_path = manifest.write_manifest(path=my_file_destination)
        self.assertEqual(my_file_destination, file_path)
        self.assertTrue(os.path.exists(file_path))
        data = manifest.read_manifest(file_path)
        os.remove(my_file_destination)
        self.assertTrue(manifest.check_manifest(data))

    def test_write_manifest_with_version(self):
        my_file_destination = tempfile.NamedTemporaryFile().name

        file_path = manifest.write_manifest(path=my_file_destination,
                                            version=manifest_version)

        self.assertEqual(my_file_destination, file_path)
        self.assertTrue(os.path.exists(file_path))
        data = manifest.read_manifest(file_path)
        os.remove(my_file_destination)
        self.assertTrue(manifest.check_manifest(data))

    def test_write_manifest_with_bad_version(self):
        my_file_destination = tempfile.NamedTemporaryFile().name

        with self.assertRaises(manifest.ManifestException):
            file_path = manifest.write_manifest(path=my_file_destination,
                                                version="0.0")
        self.assertFalse(os.path.exists(my_file_destination))

    def test_0_check_schema(self):
        # Checks sample manifest with schema
        jsonschema.Draft202012Validator.check_schema(self.schema)

    def test_10_check_manifest_ko(self):
        path = os.path.join(_json_sample_path(), 'test_manifest_ko.json')
        self.assertFalse(manifest.check_manifest(path))

    def test_10_check_manifest_ko_verbose(self):
        path = os.path.join(_json_sample_path(), 'test_manifest_ko.json')
        with open(path, 'r') as f:
            data = json.load(f)
            self.assertFalse(manifest.check_manifest(data, verbose=True))

    def test_10_check_manifest_ok(self):
        path = os.path.join(_json_sample_path(), 'test_manifest_minimum.json')
        with open(path, 'r') as f:
            data = json.load(f)
            self.assertTrue(manifest.check_manifest(data,
                                                    version='1.0'))

    def test_10_check_manifest_ok_verbose(self):
        path = os.path.join(_json_sample_path(), 'test_manifest_minimum.json')
        with open(path, 'r') as f:
            data = json.load(f)
            self.assertTrue(manifest.check_manifest(data,
                                                    verbose=True,
                                                    version='1.0'))

    def test_1_check_sample_full(self):
        # Load manifest sample
        path = os.path.join(_json_sample_path(), 'test_manifest_full.json')
        with open(path) as fp:
            # Checks sample manifest with schema
            jsonschema.validate(instance=json.load(fp), schema=self.schema)

    def test_1_check_sample_minimum(self):
        # Load manifest sample
        path = os.path.join(_json_sample_path(), 'test_manifest_minimum.json')
        with open(path) as fp:
            # Checks sample manifest with schema
            jsonschema.validate(instance=json.load(fp), schema=self.schema)

    def test_2_check_model_retrieval(self):
        # Load manifest sample
        path = os.path.join(_json_sample_path(), 'test_manifest_full.json')
        m = manifest.read_manifest(path)
        self.assertEqual(m['models']['type'], 'nifi')
        self.assertEqual(m['models']['parameters']['parameters1'], 10)
        self.assertEqual(m['models']['parameters']['parameters2'], 'hello')
        self.assertEqual(m['models']['parameters']['parameters3']['Dict']
                         ['subparameters1'], 10)
