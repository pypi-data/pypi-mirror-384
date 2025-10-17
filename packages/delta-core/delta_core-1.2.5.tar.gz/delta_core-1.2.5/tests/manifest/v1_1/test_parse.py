import os.path
import unittest
from delta.manifest import parse
from delta.manifest.parser import (
    Copyright, Input, InputModel, License, Manifest, Model, Output,
    OutputModel, Resource
)


class TestParserV1v1(unittest.TestCase):
    full = None

    @classmethod
    def setUpClass(cls):
        cls.full = os.path.join(os.path.dirname(__file__),
                                'test_manifest_full.json')

    def test_parse(self):
        expected_name = "testDeltaTwin"
        expected_description = 'Any description'

        expected_license = License(
            name="LGPLv3",
            description="license description",
            url="https://www.gnu.org/licenses/gpl-3.0.txt",
            copyrights=[Copyright(company="Gael Systems", years=[2023])]
        )

        resources = [
            Resource(
                name="aData",
                type="Data",
                description="resource data description",
                value="https://domain.net/path/data"
            ),
            Resource(
                name="aValue",
                type="string",
                value="Value"
            )
        ]
        expected_resource = {e.name: e for e in resources}

        inputs = [
            Input(name="in_data", type="Data"),
            Input(name="in_bool", type="boolean", value=False)
        ]
        expected_inputs = {e.name: e for e in inputs}

        outputs = [Output(name="out_data", type="Data")]
        expected_outputs = {e.name: e for e in outputs}

        json_formatter = Model(
            path="models/jsonFormatter",
            type="python",
            parameters={
                "image": "python:3.10",
                "cmd": "python -m json.tool"
            },
            inputs={
                "sortedKeys": InputModel(
                    name="sortedKeys",
                    type="boolean",
                    value=False,
                    prefix="--sorted-keys"
                ),
                "json": InputModel(
                    name="json",
                    type="Data"
                )
            },
            outputs={"out": OutputModel(name="out", type="stdout")}
        )
        band_selector = Model(
            path="models/band-selector",
            type="python",
            parameters={
                "image": "python:3.8",
                "requirementFiles": ["requirements.txt"],
                "pyFile": "band_extractor.py",
                "cmd": "python $(parameters.pyFile)"
            },
            inputs={
                "product": InputModel(
                    name="product",
                    type="Data"
                ),
                "bandName": InputModel(
                    name="bandName",
                    type="string"
                )
            },
            outputs={
                "selectedBand": OutputModel(
                    name="selectedBand",
                    type="Data",
                    glob="band/*"
                )
            }
        )
        expected_models = {
            "json-formatter": json_formatter,
            "band-selector": band_selector
        }

        expected_dependencies = [
            "test-deltatwin1==1.0.0",
            "test-deltatwin2==1.0.1"
        ]

        expected_manifest = Manifest(
            name=expected_name,
            description=expected_description,
            license=expected_license,
            resources=expected_resource,
            inputs=expected_inputs,
            outputs=expected_outputs,
            models=expected_models,
            dependencies=expected_dependencies
        )

        manifest = parse(self.full)
        self.assertIsNotNone(manifest)
        self.assertIsInstance(manifest, Manifest)
        self.assertEqual(expected_name, manifest.name)
        self.assertEqual(expected_description, manifest.description)
        self.assertEqual(expected_license, manifest.license)
        self.assertEqual(expected_resource, manifest.resources)
        self.assertEqual(expected_inputs, manifest.inputs)
        self.assertEqual(expected_outputs, manifest.outputs)
        self.assertEqual(expected_models, manifest.models)
        self.assertEqual(expected_dependencies, manifest.dependencies)
        self.assertEqual(expected_manifest, manifest)
