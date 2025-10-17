import os
from unittest import TestCase

from delta.manifest import parse
from delta.manifest.parser import Copyright, License, Manifest, Model, Resource


def _json_sample_path():
    return os.path.join(os.path.dirname(__file__))


class TestParse(TestCase):
    path_full = None
    path_minimum = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.path_full = os.path.join(
            _json_sample_path(), 'test_manifest_full.json')
        cls.path_minimum = os.path.join(
            _json_sample_path(), 'test_manifest_minimum.json')

    def test_description(self):
        manifest = parse(self.path_full)
        self.assertEqual(manifest.name, 'Delta Twin name')
        self.assertEqual(manifest.description, 'Delta Twin Description')
        expected_license = License(
            name='My own licence',
            description='description of the licences',
            url='http://path_to_the_licence',
            copyrights=[
                Copyright(company='Gael Systems',
                          years=[2021, 2022, 2023, 2024]),
                Copyright(company='ESA/ESRIN', years=[2021])
            ]
        )
        self.assertEqual(expected_license, manifest.license)

    def test_resources(self):
        # check on minimal manifest
        resources = parse(self.path_minimum).resources
        self.assertIsInstance(resources, dict)
        self.assertEqual({}, resources)

        # check on complete manifest
        resources = parse(self.path_full).resources
        self.assertIsInstance(resources, dict)
        self.assertEqual(len(resources), 3)

        name = ("S2B_MSIL1C_20210211T095029_N0209_R079_T33TWF"
                "_20210211T111431.zip")
        resource = resources.get(name)
        self.assertIsNotNone(resource)
        self.assertIsInstance(resource, Resource)
        self.assertEqual(resource.name, name)
        resource_value = ("${remote_service}/Product"
                          "('93d1ea14-e76b-4268-8332-8ab5070aa0cc')")
        self.assertEqual(resource_value, resource.value)

    def test_models(self):
        models = parse(self.path_minimum).models
        self.assertIsInstance(models, dict)
        self.assertEqual({}, models)

        models = parse(self.path_full).models
        self.assertIsInstance(models, dict)
        self.assertNotEqual({}, models)
        expected_model = Model(
            path='models',
            type='nifi',
            parameters={
                'parameters1': 10,
                'parameters2': 'hello',
                'parameters3': {
                    'Hello': 'World',
                    'Dict': {
                        'subparameters1': 10,
                        'subparameters2': 'test',
                    }
                },
                'parameters4': ['Hello', 'World'],
            }
        )
        self.assertEqual(expected_model, models.get("single_model"))

    def test_manifest(self):
        manifest = parse(self.path_full)
        self.assertIsInstance(manifest, Manifest)

        self.assertIsInstance(manifest.name, str)
        self.assertEqual('Delta Twin name', manifest.name)

        self.assertIsInstance(manifest.description, str)
        self.assertEqual('Delta Twin Description', manifest.description)

        self.assertIsInstance(manifest.license, License)

        self.assertIsInstance(manifest.resources, dict)
        self.assertEqual(3, len(manifest.resources))

        self.assertIsInstance(manifest.models, dict)
        self.assertEqual(1, len(manifest.models))
        self.assertIsNotNone(manifest.models.get("single_model"))

        self.assertIsInstance(manifest.dependencies, dict)
        self.assertEqual(0, len(manifest.dependencies))
